"""Event bus for event-driven workflow orchestration.

Upgrades the legacy MessageBus into an async, typed event system that
drives the agent workflow.  Events are the only mechanism for
cross-agent communication.
"""

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Awaitable, Callable

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Workflow event types.

    Each event represents a state transition in the project lifecycle.
    Agents subscribe to specific event types and publish new events
    when they complete their work.
    """

    PROJECT_CREATED = "project_created"
    SPEC_GENERATED = "spec_generated"
    ARCHITECTURE_GENERATED = "architecture_generated"
    CODE_GENERATED = "code_generated"
    SYNTAX_CHECKED = "syntax_checked"
    REVIEW_COMPLETED = "review_completed"
    ITERATION_STARTED = "iteration_started"
    WORKFLOW_COMPLETED = "workflow_completed"
    ERROR = "error"


@dataclass
class Event:
    """A workflow event.

    Events are immutable once created.  Handlers may read the payload
    but must not mutate it — produce a new event instead.
    """

    type: EventType
    project_id: str
    payload: dict = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    def with_payload(self, **updates) -> "Event":
        """Return a new Event with updated payload (immutable update)."""
        new_payload = {**self.payload, **updates}
        return Event(
            type=self.type,
            project_id=self.project_id,
            payload=new_payload,
            timestamp=self.timestamp,
            id=self.id,
        )


# Type alias for async event handlers
EventHandler = Callable[[Event], Awaitable[Event | None]]


class EventBus:
    """Async event bus with subscription-based routing.

    Handlers are registered per event type.  When an event is published,
    all handlers for that type are invoked concurrently via asyncio.gather.
    Handlers may return new events which are automatically published.
    """

    def __init__(self):
        self._handlers: dict[EventType, list[EventHandler]] = {}
        self._history: dict[str, list[Event]] = {}  # project_id -> events
        self._lock = asyncio.Lock()

    def subscribe(self, event_type: EventType, handler: EventHandler) -> None:
        """Subscribe a handler to an event type.

        A single handler may be subscribed multiple times (idempotent
        behaviour is the handler's responsibility).
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
        logger.debug("Subscribed handler to %s", event_type.value)

    def unsubscribe(self, event_type: EventType, handler: EventHandler) -> None:
        """Remove a handler from an event type."""
        if event_type in self._handlers:
            self._handlers[event_type] = [
                h for h in self._handlers[event_type] if h is not handler
            ]

    async def publish(self, event: Event) -> list[Event]:
        """Publish an event to all subscribed handlers.

        Returns:
            A list of follow-up events produced by handlers.
        """
        # Persist to history
        async with self._lock:
            if event.project_id not in self._history:
                self._history[event.project_id] = []
            self._history[event.project_id].append(event)

        handlers = self._handlers.get(event.type, [])
        if not handlers:
            logger.debug("No handlers for %s", event.type.value)
            return []

        logger.debug(
            "Publishing %s to %d handler(s) for project %s",
            event.type.value,
            len(handlers),
            event.project_id,
        )

        # Invoke handlers concurrently
        results = await asyncio.gather(
            *[self._invoke_handler(h, event) for h in handlers],
            return_exceptions=True,
        )

        follow_ups: list[Event] = []
        for result in results:
            if isinstance(result, Exception):
                logger.exception("Handler failed for %s", event.type.value)
                # Produce an error event
                follow_ups.append(
                    Event(
                        type=EventType.ERROR,
                        project_id=event.project_id,
                        payload={"original_event": event.type.value, "error": str(result)},
                    )
                )
            elif result is not None:
                follow_ups.append(result)

        # Auto-publish follow-up events
        for follow_up in follow_ups:
            asyncio.create_task(self.publish(follow_up))

        return follow_ups

    async def _invoke_handler(
        self, handler: EventHandler, event: Event
    ) -> Event | None:
        """Invoke a single handler, catching exceptions."""
        return await handler(event)

    def get_history(self, project_id: str) -> list[Event]:
        """Get the event history for a project."""
        return list(self._history.get(project_id, []))

    def clear_history(self, project_id: str) -> None:
        """Clear the event history for a project."""
        self._history.pop(project_id, None)
