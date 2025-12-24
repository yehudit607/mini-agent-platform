import hashlib
from typing import Optional

from app.models.agent import Agent


class MockLLMAdapter:
    """Generates deterministic responses based on agent config and prompt hash."""

    def generate(
        self,
        agent: Agent,
        prompt: str,
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> str:
        tool_names = [link.tool.name for link in agent.tool_links]
        tools_str = ", ".join(tool_names) if tool_names else "none"

        prompt_preview = prompt[:100] + "..." if len(prompt) > 100 else prompt

        hash_input = f"{agent.id}:{prompt}:{model}"
        response_hash = hashlib.md5(hash_input.encode()).hexdigest()[:8]

        # Build params string for demo visibility
        params_str = f"temp={temperature}"
        if max_tokens:
            params_str += f", max_tokens={max_tokens}"

        if tool_names:
            response = (
                f"[Mock Response] Agent '{agent.name}' (role: {agent.role}) "
                f"processed your request using tools: [{tools_str}]. "
                f"Based on the task '{prompt_preview}', here is a simulated response "
                f"demonstrating the agent's capabilities. "
                f"[{params_str}] [Response ID: {response_hash}]"
            )
        else:
            response = (
                f"[Mock Response] Agent '{agent.name}' (role: {agent.role}) "
                f"processed your request with no tools available. "
                f"Based on the task '{prompt_preview}', here is a simulated response. "
                f"[{params_str}] [Response ID: {response_hash}]"
            )

        return response


mock_llm_adapter = MockLLMAdapter()
