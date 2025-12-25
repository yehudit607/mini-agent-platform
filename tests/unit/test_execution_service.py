"""Unit tests for ExecutionService."""

import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone

from app.exceptions import RateLimitExceededError, ValidationError
from app.services.execution_service import ExecutionService
from app.services.rate_limit_backend import RateLimitResult
from app.schemas.execution import ExecutionRequest


class TestExecutionService:
    """Tests for ExecutionService with mocked dependencies."""

    @pytest.fixture
    def mock_llm_provider(self):
        """Create mock LLM provider."""
        provider = MagicMock()
        provider.generate = AsyncMock(return_value="Mock LLM response")
        return provider

    @pytest.fixture
    def mock_rate_limiter(self):
        """Create mock rate limiter."""
        limiter = MagicMock()
        limiter.check_and_consume = AsyncMock(
            return_value=RateLimitResult(allowed=True, remaining=99, retry_after=0)
        )
        return limiter

    @pytest.fixture
    def mock_agent_service(self):
        """Create mock agent service."""
        service = MagicMock()
        service.get_agent_for_execution = AsyncMock()
        return service

    @pytest.fixture
    def mock_log_repository(self):
        """Create mock execution log repository."""
        repo = MagicMock()
        repo.create = AsyncMock()
        return repo

    def create_mock_agent(self, name="Test Agent", tools=None):
        """Helper to create a mock agent."""
        agent = MagicMock()
        agent.id = uuid4()
        agent.name = name
        agent.role = "assistant"
        agent.tool_links = []

        if tools:
            for tool_name in tools:
                link = MagicMock()
                link.tool = MagicMock()
                link.tool.name = tool_name
                agent.tool_links.append(link)

        return agent

    def create_mock_execution_log(self, execution_id=None):
        """Helper to create a mock execution log."""
        log = MagicMock()
        log.id = execution_id or uuid4()
        log.created_at = datetime.now(timezone.utc)
        return log

    @pytest.mark.asyncio
    async def test_execute_agent_success(
        self,
        mock_llm_provider,
        mock_rate_limiter,
        mock_agent_service,
        mock_log_repository,
    ):
        """execute_agent returns response and remaining rate limit for valid request."""
        tenant_id = uuid4()
        agent_id = uuid4()
        agent = self.create_mock_agent(tools=["search", "calculator"])
        execution_log = self.create_mock_execution_log()

        mock_agent_service.get_agent_for_execution.return_value = agent
        mock_log_repository.create.return_value = execution_log

        service = ExecutionService(
            mock_agent_service, mock_log_repository, mock_llm_provider, mock_rate_limiter
        )

        request = ExecutionRequest(prompt="Test prompt", model="gpt-4o-mini")
        result, remaining = await service.execute_agent(tenant_id, agent_id, request)

        assert result.execution_id == execution_log.id
        assert result.agent_id == agent.id
        assert result.agent_name == "Test Agent"
        assert result.response == "Mock LLM response"
        assert result.tools_available == ["search", "calculator"]
        assert result.warning is None
        assert remaining == 99

    @pytest.mark.asyncio
    async def test_execute_agent_checks_rate_limit(
        self, mock_llm_provider, mock_rate_limiter, mock_agent_service, mock_log_repository
    ):
        """execute_agent checks rate limit before execution."""
        service = ExecutionService(
            mock_agent_service, mock_log_repository, mock_llm_provider, mock_rate_limiter
        )
        tenant_id = uuid4()
        agent_id = uuid4()
        request = ExecutionRequest(prompt="Test", model="gpt-4o-mini")

        # Should call rate limiter
        mock_rate_limiter.check_and_consume.return_value = RateLimitResult(
            allowed=True, remaining=50, retry_after=0
        )

        try:
            await service.execute_agent(tenant_id, agent_id, request)
        except Exception:
            pass  # We expect this to fail due to missing mocks

        mock_rate_limiter.check_and_consume.assert_called_once_with(tenant_id)

    @pytest.mark.asyncio
    async def test_execute_agent_rate_limit_exceeded(
        self, mock_llm_provider, mock_rate_limiter, mock_agent_service, mock_log_repository
    ):
        """execute_agent raises RateLimitExceededError when limit exceeded."""
        mock_rate_limiter.check_and_consume.return_value = RateLimitResult(
            allowed=False, remaining=0, retry_after=30
        )

        service = ExecutionService(
            mock_agent_service, mock_log_repository, mock_llm_provider, mock_rate_limiter
        )
        tenant_id = uuid4()
        agent_id = uuid4()
        request = ExecutionRequest(prompt="Test", model="gpt-4o-mini")

        with pytest.raises(RateLimitExceededError) as exc_info:
            await service.execute_agent(tenant_id, agent_id, request)

        assert exc_info.value.details["retry_after_seconds"] == 30

    @pytest.mark.asyncio
    async def test_execute_agent_calls_llm_provider(
        self,
        mock_llm_provider,
        mock_rate_limiter,
        mock_agent_service,
        mock_log_repository,
    ):
        """execute_agent calls LLM provider with correct parameters."""
        agent = self.create_mock_agent()
        execution_log = self.create_mock_execution_log()

        mock_agent_service.get_agent_for_execution.return_value = agent
        mock_log_repository.create.return_value = execution_log

        service = ExecutionService(
            mock_agent_service, mock_log_repository, mock_llm_provider, mock_rate_limiter
        )

        request = ExecutionRequest(
            prompt="Test prompt",
            model="gpt-4o-mini",
            temperature=0.5,
            max_tokens=100,
        )

        await service.execute_agent(uuid4(), uuid4(), request)

        mock_llm_provider.generate.assert_called_once()
        call_kwargs = mock_llm_provider.generate.call_args[1]
        assert call_kwargs["agent"] == agent
        assert call_kwargs["prompt"] == "Test prompt"
        assert call_kwargs["model"] == "gpt-4o-mini"
        assert call_kwargs["temperature"] == 0.5
        assert call_kwargs["max_tokens"] == 100

    @pytest.mark.asyncio
    async def test_execute_agent_creates_execution_log(
        self,
        mock_llm_provider,
        mock_rate_limiter,
        mock_agent_service,
        mock_log_repository,
    ):
        """execute_agent creates execution log."""
        tenant_id = uuid4()
        agent_id = uuid4()
        agent = self.create_mock_agent()
        execution_log = self.create_mock_execution_log()

        mock_agent_service.get_agent_for_execution.return_value = agent
        mock_log_repository.create.return_value = execution_log

        service = ExecutionService(
            mock_agent_service, mock_log_repository, mock_llm_provider, mock_rate_limiter
        )

        request = ExecutionRequest(prompt="Test prompt", model="gpt-4o-mini")
        await service.execute_agent(tenant_id, agent_id, request)

        mock_log_repository.create.assert_called_once()
        call_kwargs = mock_log_repository.create.call_args[1]
        assert call_kwargs["tenant_id"] == tenant_id
        assert call_kwargs["agent_id"] == agent_id
        assert call_kwargs["prompt"] == "Test prompt"
        assert call_kwargs["model"] == "gpt-4o-mini"
        assert call_kwargs["response"] == "Mock LLM response"

    @pytest.mark.asyncio
    async def test_execute_agent_warning_for_no_tools(
        self,
        mock_llm_provider,
        mock_rate_limiter,
        mock_agent_service,
        mock_log_repository,
    ):
        """execute_agent includes warning when agent has no tools."""
        agent = self.create_mock_agent(tools=[])  # No tools
        execution_log = self.create_mock_execution_log()

        mock_agent_service.get_agent_for_execution.return_value = agent
        mock_log_repository.create.return_value = execution_log

        service = ExecutionService(
            mock_agent_service, mock_log_repository, mock_llm_provider, mock_rate_limiter
        )

        request = ExecutionRequest(prompt="Test", model="gpt-4o-mini")
        result, remaining = await service.execute_agent(uuid4(), uuid4(), request)

        assert result.warning is not None
        assert "no tools configured" in result.warning
        assert result.tools_available == []

    @pytest.mark.asyncio
    async def test_execute_agent_returns_rate_limit_remaining(
        self,
        mock_llm_provider,
        mock_rate_limiter,
        mock_agent_service,
        mock_log_repository,
    ):
        """execute_agent returns remaining rate limit tokens."""
        agent = self.create_mock_agent()
        execution_log = self.create_mock_execution_log()

        mock_agent_service.get_agent_for_execution.return_value = agent
        mock_log_repository.create.return_value = execution_log
        mock_rate_limiter.check_and_consume.return_value = RateLimitResult(
            allowed=True, remaining=42, retry_after=0
        )

        service = ExecutionService(
            mock_agent_service, mock_log_repository, mock_llm_provider, mock_rate_limiter
        )

        request = ExecutionRequest(prompt="Test", model="gpt-4o-mini")
        result, remaining = await service.execute_agent(uuid4(), uuid4(), request)

        assert remaining == 42
