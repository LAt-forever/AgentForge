"""Agent plugin interface for the event-driven workflow.

Any agent that participates in the event-driven workflow must implement
AgentPlugin.  Existing agents subclass BaseAgent and are wrapped
automatically by built-in plugins.
"""

from abc import ABC, abstractmethod

from backend.agents.base_agent import AgentContext, AgentOutput
from backend.core.event_bus import Event, EventType


class AgentPlugin(ABC):
    """Interface for agent plugins in the event-driven workflow.

    A plugin declares what event types it consumes and what event type
    it produces.  The orchestrator routes events to the appropriate
    plugin based on these declarations.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique plugin name (e.g. 'pm', 'coder', 'security-reviewer')."""

    @property
    @abstractmethod
    def consumes(self) -> list[EventType]:
        """Event types this plugin subscribes to."""

    @property
    @abstractmethod
    def produces(self) -> EventType | None:
        """Event type published when this plugin completes.

        Returns None for terminal plugins that don't produce follow-up events.
        """

    @abstractmethod
    async def execute(self, context: AgentContext, event: Event) -> AgentOutput:
        """Execute the plugin's logic.

        Args:
            context: Execution context with accumulated outputs.
            event: The triggering event (type is in consumes).

        Returns:
            The agent's output.
        """


class BaseAgentPlugin(AgentPlugin):
    """Convenience base that wraps an existing BaseAgent subclass.

    Built-in agents (PMAgent, ArchitectAgent, etc.) subclass BaseAgent.
    BaseAgentPlugin bridges them into the plugin system by delegating
    execute() to the wrapped agent's run().
    """

    def __init__(self, agent_cls, llm_client):
        self._agent_cls = agent_cls
        self._llm_client = llm_client
        self._agent = None  # lazy init

    @property
    def name(self) -> str:
        return self._agent_cls.__name__.lower().replace("agent", "")

    @property
    def consumes(self) -> list[EventType]:
        return []

    @property
    def produces(self) -> EventType | None:
        return None

    async def execute(self, context: AgentContext, event: Event) -> AgentOutput:
        """Delegate to the wrapped BaseAgent.run()."""
        if self._agent is None:
            self._agent = self._agent_cls(self._llm_client)
        return await self._agent.run(context)
