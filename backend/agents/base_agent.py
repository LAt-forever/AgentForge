"""Base agent class for the DevAgent Team."""

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from backend.llm.client import LLMClient
from backend.llm.models import LLMConfig


@dataclass
class AgentContext:
    """Context passed to an Agent during execution."""

    requirement: str
    project_id: str
    spec: str = ""  # PM Agent output
    architecture: str = ""  # Architect Agent output
    code: dict = field(default_factory=dict)  # Coder Agent output: {filepath: content}
    review_feedback: str = ""  # Reviewer Agent output (for iteration)
    iteration: int = 0


@dataclass
class AgentOutput:
    """Output produced by an Agent."""

    content: str = ""  # Primary text output
    files: dict = field(default_factory=dict)  # Generated files: {filepath: content}
    metadata: dict = field(default_factory=dict)  # Additional metadata


class BaseAgent(ABC):
    """Abstract base class for all agents."""

    def __init__(self, name: str, llm_client: LLMClient):
        self.name = name
        self.llm = llm_client

    @abstractmethod
    async def run(self, context: AgentContext) -> AgentOutput:
        """Execute the agent's task.

        Args:
            context: The execution context containing inputs from previous agents.

        Returns:
            The agent's output.
        """
        pass

    def _load_prompt(self, prompt_name: str) -> str:
        """Load a prompt template from the prompts directory.

        Args:
            prompt_name: Name of the prompt file (without .txt extension).

        Returns:
            The prompt text content.
        """
        prompt_path = os.path.join(
            os.path.dirname(__file__), "..", "llm", "prompts", f"{prompt_name}.txt"
        )
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read()

    async def _call_llm(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str = "",
        temperature: float = 0.7,
    ) -> str:
        """Call the LLM with the given prompts.

        Args:
            system_prompt: The system prompt to use.
            user_prompt: The user prompt to send.
            model: Model identifier (defaults to claude-3-5-sonnet-20241022).
            temperature: Sampling temperature.

        Returns:
            The LLM response content.
        """
        config = LLMConfig(
            model=model or "claude-3-5-sonnet-20241022",
            temperature=temperature,
            max_tokens=4096,
            system_prompt=system_prompt,
        )
        response = await self.llm.call(user_prompt, config)
        return response.content
