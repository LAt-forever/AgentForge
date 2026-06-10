"""Tests for EventBus."""

import asyncio

import pytest

from backend.core.event_bus import Event, EventBus, EventType


@pytest.fixture
def bus():
    return EventBus()


class TestEventBusPublishSubscribe:
    """Test basic publish/subscribe."""

    @pytest.mark.asyncio
    async def test_subscribe_and_publish(self, bus):
        """Handler receives published events."""
        received = []

        async def handler(event):
            received.append(event)
            return None

        bus.subscribe(EventType.SPEC_GENERATED, handler)
        event = Event(type=EventType.SPEC_GENERATED, project_id="p1", payload={"spec": "test"})
        await bus.publish(event)

        assert len(received) == 1
        assert received[0].type == EventType.SPEC_GENERATED
        assert received[0].project_id == "p1"

    @pytest.mark.asyncio
    async def test_multiple_handlers(self, bus):
        """Multiple handlers for same event type all fire."""
        calls = []

        async def h1(event):
            calls.append("h1")
            return None

        async def h2(event):
            calls.append("h2")
            return None

        bus.subscribe(EventType.SPEC_GENERATED, h1)
        bus.subscribe(EventType.SPEC_GENERATED, h2)
        await bus.publish(Event(type=EventType.SPEC_GENERATED, project_id="p1"))

        assert sorted(calls) == ["h1", "h2"]

    @pytest.mark.asyncio
    async def test_unsubscribe(self, bus):
        """Unsubscribed handler no longer receives events."""
        received = []

        async def handler(event):
            received.append(event)
            return None

        bus.subscribe(EventType.SPEC_GENERATED, handler)
        bus.unsubscribe(EventType.SPEC_GENERATED, handler)
        await bus.publish(Event(type=EventType.SPEC_GENERATED, project_id="p1"))

        assert len(received) == 0

    @pytest.mark.asyncio
    async def test_no_handlers_no_crash(self, bus):
        """Publishing with no subscribers is safe."""
        event = Event(type=EventType.SPEC_GENERATED, project_id="p1")
        result = await bus.publish(event)
        assert result == []


class TestEventBusFollowUpEvents:
    """Test follow-up event auto-publishing."""

    @pytest.mark.asyncio
    async def test_handler_produces_follow_up(self, bus):
        """Handler returning an event auto-publishes it."""
        received_spec = []
        received_arch = []

        async def spec_handler(event):
            received_spec.append(event)
            return Event(type=EventType.ARCHITECTURE_GENERATED, project_id=event.project_id)

        async def arch_handler(event):
            received_arch.append(event)
            return None

        bus.subscribe(EventType.SPEC_GENERATED, spec_handler)
        bus.subscribe(EventType.ARCHITECTURE_GENERATED, arch_handler)

        await bus.publish(Event(type=EventType.SPEC_GENERATED, project_id="p1"))
        # Allow auto-publish to complete
        await asyncio.sleep(0.1)

        assert len(received_spec) == 1
        assert len(received_arch) == 1

    @pytest.mark.asyncio
    async def test_handler_exception_produces_error_event(self, bus):
        """Handler exception produces ERROR event."""
        received_errors = []

        async def failing_handler(event):
            raise ValueError("boom")

        async def error_handler(event):
            received_errors.append(event)
            return None

        bus.subscribe(EventType.SPEC_GENERATED, failing_handler)
        bus.subscribe(EventType.ERROR, error_handler)

        await bus.publish(Event(type=EventType.SPEC_GENERATED, project_id="p1"))
        await asyncio.sleep(0.1)

        assert len(received_errors) == 1
        assert received_errors[0].type == EventType.ERROR
        assert "boom" in received_errors[0].payload["error"]


class TestEventBusHistory:
    """Test event history."""

    @pytest.mark.asyncio
    async def test_history_recorded(self, bus):
        """Events are persisted to history."""
        async def handler(event):
            return None

        bus.subscribe(EventType.SPEC_GENERATED, handler)
        await bus.publish(Event(type=EventType.SPEC_GENERATED, project_id="p1"))

        history = bus.get_history("p1")
        assert len(history) == 1
        assert history[0].type == EventType.SPEC_GENERATED

    @pytest.mark.asyncio
    async def test_history_per_project(self, bus):
        """History is isolated per project."""
        async def handler(event):
            return None

        bus.subscribe(EventType.SPEC_GENERATED, handler)
        await bus.publish(Event(type=EventType.SPEC_GENERATED, project_id="p1"))
        await bus.publish(Event(type=EventType.SPEC_GENERATED, project_id="p2"))

        assert len(bus.get_history("p1")) == 1
        assert len(bus.get_history("p2")) == 1

    @pytest.mark.asyncio
    async def test_clear_history(self, bus):
        """History can be cleared."""
        async def handler(event):
            return None

        bus.subscribe(EventType.SPEC_GENERATED, handler)
        await bus.publish(Event(type=EventType.SPEC_GENERATED, project_id="p1"))
        bus.clear_history("p1")
        assert bus.get_history("p1") == []


class TestEvent:
    """Test Event dataclass."""

    def test_event_has_id_and_timestamp(self):
        """Events auto-generate id and timestamp."""
        event = Event(type=EventType.PROJECT_CREATED, project_id="p1")
        assert event.id
        assert isinstance(event.id, str)
        assert event.timestamp > 0

    def test_with_payload(self):
        """Immutable payload update."""
        event = Event(type=EventType.PROJECT_CREATED, project_id="p1", payload={"a": 1})
        new_event = event.with_payload(b=2)
        assert new_event.payload == {"a": 1, "b": 2}
        assert event.payload == {"a": 1}  # Original unchanged
