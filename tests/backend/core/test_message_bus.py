"""Tests for the MessageBus."""

import pytest

from backend.core.message_bus import Message, MessageBus


class TestPublishAndSubscribe:
    """Test basic publish and subscribe."""

    def test_publish_and_subscribe(self):
        """Subscribe to a channel, publish a message, verify received."""
        bus = MessageBus()
        received = []

        def handler(msg):
            received.append(msg)

        bus.subscribe("test_channel", handler)
        msg = Message(type="test", sender="alice", content="hello")
        bus.publish("test_channel", msg)

        assert len(received) == 1
        assert received[0].type == "test"
        assert received[0].sender == "alice"
        assert received[0].content == "hello"


class TestMultipleSubscribers:
    """Test multiple subscribers on the same channel."""

    def test_multiple_subscribers(self):
        """Two subscribers on same channel both receive the message."""
        bus = MessageBus()
        received_a = []
        received_b = []

        def handler_a(msg):
            received_a.append(msg)

        def handler_b(msg):
            received_b.append(msg)

        bus.subscribe("test_channel", handler_a)
        bus.subscribe("test_channel", handler_b)
        msg = Message(type="test", sender="bob", content="hi")
        bus.publish("test_channel", msg)

        assert len(received_a) == 1
        assert len(received_b) == 1
        assert received_a[0].content == "hi"
        assert received_b[0].content == "hi"


class TestNoSubscriber:
    """Test publishing to a channel with no subscribers."""

    def test_no_subscriber_no_crash(self):
        """Publish to channel with no subscribers should not raise."""
        bus = MessageBus()
        msg = Message(type="test", sender="alice", content="hello")

        # Should not raise
        bus.publish("empty_channel", msg)


class TestUnsubscribe:
    """Test unsubscribing a handler."""

    def test_unsubscribe(self):
        """Unsubscribe a handler, it should no longer receive messages."""
        bus = MessageBus()
        received = []

        def handler(msg):
            received.append(msg)

        bus.subscribe("test_channel", handler)
        bus.unsubscribe("test_channel", handler)
        msg = Message(type="test", sender="alice", content="hello")
        bus.publish("test_channel", msg)

        assert len(received) == 0
