"""Built-in agent plugins for the event-driven workflow.

Each built-in plugin wraps an existing BaseAgent subclass and declares
the event types it consumes and produces.
"""

from backend.agents.architect_agent import ArchitectAgent
from backend.agents.coder_agent import CoderAgent
from backend.agents.pm_agent import PMAgent
from backend.agents.reviewer_agent import ReviewerAgent
from backend.core.event_bus import EventType

from .plugins import (
    ArchitectPlugin,
    CoderPlugin,
    PMPlugin,
    ReviewerPlugin,
)

__all__ = [
    "PMPlugin",
    "ArchitectPlugin",
    "CoderPlugin",
    "ReviewerPlugin",
    "register_built_in_plugins",
]


def register_built_in_plugins(registry, llm_client) -> None:
    """Register all built-in plugins to a PluginRegistry.

    Args:
        registry: PluginRegistry instance to register to.
        llm_client: LLMClient instance to pass to each plugin.
    """
    registry.register(PMPlugin(llm_client))
    registry.register(ArchitectPlugin(llm_client))
    registry.register(CoderPlugin(llm_client))
    registry.register(ReviewerPlugin(llm_client))
