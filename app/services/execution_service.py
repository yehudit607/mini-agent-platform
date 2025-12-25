"""Agent execution service."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.llm_provider import LLMProvider
from app.config import get_settings
from app.exceptions import RateLimitExceededError, ValidationError
from app.logging_config import setup_logger
from app.repositories.execution_log_repository import ExecutionLogRepository
from app.schemas.execution import ExecutionRequest, ExecutionResponse
from app.services.agent_service import AgentService
from app.services.rate_limiter import RateLimiter

settings = get_settings()
logger = setup_logger(__name__)


class ExecutionService:
    """Service for executing agent prompts.

    Uses Dependency Injection for LLMProvider and RateLimiter,
    enabling easy testing and swapping implementations.
    """

    def __init__(
        self,
        session: AsyncSession,
        llm_provider: LLMProvider,
        rate_limiter: RateLimiter,
    ):
        self.session = session
        self.llm_provider = llm_provider
        self.rate_limiter = rate_limiter
        self.agent_service = AgentService(session)
        self.log_repository = ExecutionLogRepository(session)

    async def execute_agent(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        data: ExecutionRequest,
    ) -> ExecutionResponse:
        rate_result = await self.rate_limiter.check_and_consume(tenant_id)

        if not rate_result.allowed:
            raise RateLimitExceededError(
                retry_after=rate_result.retry_after,
                limit=settings.rate_limit_requests,
                window_seconds=settings.rate_limit_window_seconds,
            )

        agent = await self.agent_service.get_agent_for_execution(tenant_id, agent_id)

        if data.model not in settings.allowed_models:
            raise ValidationError(
                error_code="INVALID_MODEL",
                message="The specified model is not supported",
                details={
                    "provided_model": data.model,
                    "allowed_models": settings.allowed_models,
                },
            )

        logger.info(
            f"Starting agent execution: tenant_id={tenant_id}, "
            f"agent_id={agent_id}, agent_name={agent.name}, model={data.model}"
        )

        response_text = await self.llm_provider.generate(
            agent=agent,
            prompt=data.prompt,
            model=data.model,
            temperature=data.temperature,
            max_tokens=data.max_tokens,
        )

        log = await self.log_repository.create(
            tenant_id=tenant_id,
            agent_id=agent_id,
            prompt=data.prompt,
            model=data.model,
            response=response_text,
        )

        logger.info(
            f"Completed agent execution: execution_id={log.id}, "
            f"agent_name={agent.name}, response_length={len(response_text)}"
        )

        tool_names = [link.tool.name for link in agent.tool_links]
        warning = None
        if not tool_names:
            warning = (
                "This agent has no tools configured. "
                "Consider adding tools for enhanced capabilities."
            )

        return ExecutionResponse(
            execution_id=log.id,
            agent_id=agent.id,
            agent_name=agent.name,
            model=data.model,
            prompt=data.prompt,
            response=response_text,
            tools_available=tool_names,
            warning=warning,
            executed_at=log.created_at,
        )

    async def get_remaining_rate_limit(self, tenant_id: UUID) -> int:
        """Get remaining rate limit tokens for response headers."""
        return await self.rate_limiter.get_remaining(tenant_id)
