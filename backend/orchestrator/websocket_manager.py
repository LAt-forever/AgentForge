"""WebSocket connection manager for real-time updates."""

from starlette.websockets import WebSocket


class WebSocketManager:
    """Manages WebSocket connections per project."""

    def __init__(self):
        self._connections: dict[str, WebSocket] = {}

    async def connect(self, project_id: str, websocket: WebSocket) -> None:
        """Accept and store a WebSocket connection for a project."""
        await websocket.accept()
        self._connections[project_id] = websocket

    async def disconnect(self, project_id: str) -> None:
        """Remove a WebSocket connection for a project."""
        self._connections.pop(project_id, None)

    async def send_message(self, project_id: str, message: dict) -> None:
        """Send a JSON message to a specific project's WebSocket."""
        ws = self._connections.get(project_id)
        if ws is not None:
            await ws.send_json(message)

    async def broadcast(self, message: dict) -> None:
        """Send a JSON message to all connected WebSockets.

        Disconnects any connection that raises an error.
        """
        failed: list[str] = []
        for project_id, ws in self._connections.items():
            try:
                await ws.send_json(message)
            except Exception:
                failed.append(project_id)
        for project_id in failed:
            self._connections.pop(project_id, None)
