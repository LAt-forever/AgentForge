"""LLM-related data models."""

from enum import Enum
from dataclasses import dataclass


class ModelProvider(Enum):
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    DEEPSEEK = "deepseek"
    GLM = "glm"


@dataclass
class LLMResponse:
    """Standardized LLM response."""
    content: str
    model: str
    usage: dict | None = None


@dataclass
class LLMConfig:
    """Configuration for an LLM call."""
    model: str
    temperature: float = 0.7
    max_tokens: int = 4096
    system_prompt: str = ""
