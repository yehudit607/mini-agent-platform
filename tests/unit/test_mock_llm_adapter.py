"""Unit tests for MockLLMAdapter."""

import asyncio
import pytest
from uuid import uuid4
from unittest.mock import MagicMock

from app.adapters.mock_llm import MockLLMAdapter


class TestMockLLMAdapter:
    """Tests for MockLLMAdapter response generation."""

    def create_mock_agent(self, name: str, role: str, tool_names: list[str] = None):
        """Helper to create a mock agent."""
        agent = MagicMock()
        agent.id = uuid4()
        agent.name = name
        agent.role = role

        # Mock tool_links
        if tool_names:
            tool_links = []
            for tool_name in tool_names:
                link = MagicMock()
                link.tool = MagicMock()
                link.tool.name = tool_name
                tool_links.append(link)
            agent.tool_links = tool_links
        else:
            agent.tool_links = []

        return agent

    @pytest.mark.asyncio
    async def test_generates_response_with_agent_info(self):
        """Should include agent name and role in response."""
        adapter = MockLLMAdapter()
        agent = self.create_mock_agent("Test Agent", "assistant")

        response = await adapter.generate(
            agent=agent, prompt="Test prompt", model="gpt-4o-mini"
        )

        assert "Test Agent" in response
        assert "assistant" in response

    @pytest.mark.asyncio
    async def test_generates_response_with_tools(self):
        """Should include tool names when agent has tools."""
        adapter = MockLLMAdapter()
        agent = self.create_mock_agent(
            "Agent", "worker", tool_names=["search", "calculator"]
        )

        response = await adapter.generate(
            agent=agent, prompt="Test", model="gpt-4o-mini"
        )

        assert "search" in response
        assert "calculator" in response
        assert "tools:" in response.lower()

    @pytest.mark.asyncio
    async def test_generates_response_without_tools(self):
        """Should indicate no tools when agent has none."""
        adapter = MockLLMAdapter()
        agent = self.create_mock_agent("Agent", "basic")

        response = await adapter.generate(
            agent=agent, prompt="Test", model="gpt-4o-mini"
        )

        assert "no tools" in response.lower()

    @pytest.mark.asyncio
    async def test_includes_prompt_preview(self):
        """Should include prompt preview in response."""
        adapter = MockLLMAdapter()
        agent = self.create_mock_agent("Agent", "worker")

        response = await adapter.generate(
            agent=agent, prompt="Find the latest AI trends", model="gpt-4o-mini"
        )

        assert "Find the latest AI trends" in response

    @pytest.mark.asyncio
    async def test_truncates_long_prompt(self):
        """Should truncate prompt preview if longer than 100 chars."""
        adapter = MockLLMAdapter()
        agent = self.create_mock_agent("Agent", "worker")
        long_prompt = "x" * 150

        response = await adapter.generate(
            agent=agent, prompt=long_prompt, model="gpt-4o-mini"
        )

        # Should include truncation indicator
        assert "..." in response
        # Should not include full prompt
        assert long_prompt not in response

    @pytest.mark.asyncio
    async def test_includes_temperature_in_response(self):
        """Should include temperature parameter in response."""
        adapter = MockLLMAdapter()
        agent = self.create_mock_agent("Agent", "worker")

        response = await adapter.generate(
            agent=agent,
            prompt="Test",
            model="gpt-4o-mini",
            temperature=0.3,
        )

        assert "temp=0.3" in response

    @pytest.mark.asyncio
    async def test_includes_max_tokens_when_provided(self):
        """Should include max_tokens in response when provided."""
        adapter = MockLLMAdapter()
        agent = self.create_mock_agent("Agent", "worker")

        response = await adapter.generate(
            agent=agent,
            prompt="Test",
            model="gpt-4o-mini",
            temperature=0.7,
            max_tokens=500,
        )

        assert "temp=0.7" in response
        assert "max_tokens=500" in response

    @pytest.mark.asyncio
    async def test_omits_max_tokens_when_none(self):
        """Should not include max_tokens when None."""
        adapter = MockLLMAdapter()
        agent = self.create_mock_agent("Agent", "worker")

        response = await adapter.generate(
            agent=agent,
            prompt="Test",
            model="gpt-4o-mini",
            temperature=0.7,
            max_tokens=None,
        )

        assert "temp=0.7" in response
        assert "max_tokens" not in response

    @pytest.mark.asyncio
    async def test_includes_deterministic_response_id(self):
        """Should include response ID based on agent, prompt, model."""
        adapter = MockLLMAdapter()
        agent = self.create_mock_agent("Agent", "worker")

        response1 = await adapter.generate(
            agent=agent, prompt="Same prompt", model="gpt-4o-mini"
        )
        response2 = await adapter.generate(
            agent=agent, prompt="Same prompt", model="gpt-4o-mini"
        )

        # Should have Response ID
        assert "Response ID:" in response1
        assert "Response ID:" in response2
        # Should be deterministic (same ID for same input)
        assert response1 == response2

    @pytest.mark.asyncio
    async def test_different_inputs_produce_different_ids(self):
        """Should produce different IDs for different inputs."""
        adapter = MockLLMAdapter()
        agent = self.create_mock_agent("Agent", "worker")

        response1 = await adapter.generate(
            agent=agent, prompt="First prompt", model="gpt-4o-mini"
        )
        response2 = await adapter.generate(
            agent=agent, prompt="Second prompt", model="gpt-4o-mini"
        )

        assert response1 != response2

    @pytest.mark.asyncio
    async def test_simulates_async_latency(self):
        """Should simulate network latency with async sleep."""
        adapter = MockLLMAdapter()
        agent = self.create_mock_agent("Agent", "worker")

        import time

        start = time.time()
        await adapter.generate(agent=agent, prompt="Test", model="gpt-4o-mini")
        duration = time.time() - start

        # Should take at least 50ms (the sleep duration)
        assert duration >= 0.04  # Allow small margin

    @pytest.mark.asyncio
    async def test_is_truly_async(self):
        """Should allow concurrent execution."""
        adapter = MockLLMAdapter()
        agent1 = self.create_mock_agent("Agent1", "worker")
        agent2 = self.create_mock_agent("Agent2", "worker")

        # Run two generations concurrently
        task1 = adapter.generate(agent=agent1, prompt="Test1", model="gpt-4o-mini")
        task2 = adapter.generate(agent=agent2, prompt="Test2", model="gpt-4o-mini")

        results = await asyncio.gather(task1, task2)

        assert len(results) == 2
        assert "Agent1" in results[0]
        assert "Agent2" in results[1]
