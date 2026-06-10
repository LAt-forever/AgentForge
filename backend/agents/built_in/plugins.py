"""Built-in agent plugin implementations.

Each class wraps a legacy BaseAgent and maps it into the event-driven
workflow by declaring consumes / produces event types.
"""

from backend.agents.architect_agent import ArchitectAgent
from backend.agents.base_agent import AgentContext, AgentOutput
from backend.agents.coder_agent import CoderAgent
from backend.agents.pm_agent import PMAgent
from backend.agents.plugin_base import BaseAgentPlugin
from backend.agents.reviewer_agent import ReviewerAgent
from backend.core.event_bus import Event, EventType


class PMPlugin(BaseAgentPlugin):
    """Product Manager plugin: requirement -> spec."""

    def __init__(self, llm_client):
        super().__init__(PMAgent, llm_client)

    @property
    def name(self) -> str:
        return "pm"

    @property
    def consumes(self) -> list[EventType]:
        return [EventType.PROJECT_CREATED]

    @property
    def produces(self) -> EventType | None:
        return EventType.SPEC_GENERATED


class ArchitectPlugin(BaseAgentPlugin):
    """Architect plugin: spec -> architecture."""

    def __init__(self, llm_client):
        super().__init__(ArchitectAgent, llm_client)

    @property
    def name(self) -> str:
        return "architect"

    @property
    def consumes(self) -> list[EventType]:
        return [EventType.SPEC_GENERATED]

    @property
    def produces(self) -> EventType | None:
        return EventType.ARCHITECTURE_GENERATED


class CoderPlugin(BaseAgentPlugin):
    """Coder plugin: architecture (+ review feedback) -> code."""

    def __init__(self, llm_client):
        super().__init__(CoderAgent, llm_client)

    @property
    def name(self) -> str:
        return "coder"

    @property
    def consumes(self) -> list[EventType]:
        return [EventType.ARCHITECTURE_GENERATED, EventType.ITERATION_STARTED]

    @property
    def produces(self) -> EventType | None:
        return EventType.CODE_GENERATED


class ReviewerPlugin(BaseAgentPlugin):
    """Reviewer plugin: code -> review report."""

    def __init__(self, llm_client):
        super().__init__(ReviewerAgent, llm_client)

    @property
    def name(self) -> str:
        return "reviewer"

    @property
    def consumes(self) -> list[EventType]:
        return [EventType.SYNTAX_CHECKED]

    @property
    def produces(self) -> EventType | None:
        return EventType.REVIEW_COMPLETED
