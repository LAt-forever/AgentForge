"""Message Bus for inter-agent communication."""

from dataclasses import dataclass, field


@dataclass
class Message:
    """A message sent between agents."""

    type: str
    sender: str
    content: str
    metadata: dict = field(default_factory=dict)


class MessageBus:
    """Simple pub/sub message bus for agent communication."""

    def __init__(self):
        self._subscribers: dict[str, list[callable]] = {}

    def subscribe(self, channel: str, handler: callable) -> None:
        """Subscribe a handler to a channel."""
        if channel not in self._subscribers:
            self._subscribers[channel] = []
        self._subscribers[channel].append(handler)

    def publish(self, channel: str, message: Message) -> None:
        """Publish a message to a channel, calling all subscribers."""
        handlers = self._subscribers.get(channel, [])
        for handler in handlers:
            handler(message)

    def unsubscribe(self, channel: str, handler: callable) -> None:
        """Unsubscribe a handler from a channel."""
        if channel in self._subscribers:
            self._subscribers[channel] = [
                h for h in self._subscribers[channel] if h is not handler
            ]
