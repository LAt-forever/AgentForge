"""Tests for the WebSocketManager."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from backend.orchestrator.websocket_manager import WebSocketManager


class TestWebSocketManager:
    @pytest.mark.asyncio
    async def test_connect_and_disconnect(self):
        manager = WebSocketManager()
        ws = AsyncMock()

        await manager.connect("proj-1", ws)
        assert "proj-1" in manager._connections
        assert manager._connections["proj-1"] == ws
        ws.accept.assert_awaited_once()

        await manager.disconnect("proj-1")
        assert "proj-1" not in manager._connections

    @pytest.mark.asyncio
    async def test_send_message(self):
        manager = WebSocketManager()
        ws = AsyncMock()
        await manager.connect("proj-1", ws)

        message = {"type": "status", "data": "hello"}
        await manager.send_message("proj-1", message)

        ws.send_json.assert_awaited_once_with(message)

    @pytest.mark.asyncio
    async def test_broadcast(self):
        manager = WebSocketManager()
        ws1 = AsyncMock()
        ws2 = AsyncMock()
        await manager.connect("proj-1", ws1)
        await manager.connect("proj-2", ws2)

        message = {"type": "broadcast", "data": "all"}
        await manager.broadcast(message)

        ws1.send_json.assert_awaited_once_with(message)
        ws2.send_json.assert_awaited_once_with(message)

    @pytest.mark.asyncio
    async def test_broadcast_disconnects_failed(self):
        manager = WebSocketManager()
        ws_good = AsyncMock()
        ws_bad = AsyncMock()
        ws_bad.send_json = AsyncMock(side_effect=Exception("connection lost"))

        await manager.connect("proj-1", ws_good)
        await manager.connect("proj-2", ws_bad)

        message = {"type": "broadcast", "data": "all"}
        await manager.broadcast(message)

        ws_good.send_json.assert_awaited_once_with(message)
        ws_bad.send_json.assert_awaited_once_with(message)
        assert "proj-2" not in manager._connections
        assert "proj-1" in manager._connections
