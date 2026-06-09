"""Tests for the AgentScheduler."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from backend.agents.base_agent import AgentContext, AgentOutput
from backend.orchestrator.scheduler import AgentScheduler


class TestAgentScheduler:
    @pytest.mark.asyncio
    async def test_schedule_pm_agent(self):
        llm_client = MagicMock()
        ws_manager = AsyncMock()
        state_store = MagicMock()

        scheduler = AgentScheduler(llm_client, ws_manager, state_store)

        mock_output = AgentOutput(content="spec output", files={}, metadata={"agent_type": "pm"})

        mock_agent_class = MagicMock()
        mock_instance = mock_agent_class.return_value
        mock_instance.run = AsyncMock(return_value=mock_output)

        with patch.dict(
            "backend.orchestrator.scheduler.AGENT_MAP", {"pm": mock_agent_class}, clear=False
        ):
            context = AgentContext(requirement="build a thing", project_id="proj-1")
            result = await scheduler.run_agent("pm", context, "proj-1")

            mock_agent_class.assert_called_once_with(llm_client)
            mock_instance.run.assert_awaited_once_with(context)
            assert result == mock_output

            # Verify notifications
            assert ws_manager.send_message.await_count == 2
            # First call: running
            call_1 = ws_manager.send_message.await_args_list[0]
            assert call_1[0][0] == "proj-1"
            assert call_1[0][1]["type"] == "agent_status"
            assert call_1[0][1]["agent"] == "pm"
            assert call_1[0][1]["status"] == "running"

            # Second call: completed
            call_2 = ws_manager.send_message.await_args_list[1]
            assert call_2[0][0] == "proj-1"
            assert call_2[0][1]["type"] == "agent_status"
            assert call_2[0][1]["agent"] == "pm"
            assert call_2[0][1]["status"] == "completed"
            assert call_2[0][1]["output"]["summary"] == "spec output"

            # Verify state_store updated twice (running + completed)
            assert state_store.update_agent_status.call_count == 2

    @pytest.mark.asyncio
    async def test_schedule_invalid_agent(self):
        llm_client = MagicMock()
        ws_manager = AsyncMock()
        state_store = MagicMock()

        scheduler = AgentScheduler(llm_client, ws_manager, state_store)

        context = AgentContext(requirement="build a thing", project_id="proj-1")
        with pytest.raises(ValueError, match="Unknown agent: unknown"):
            await scheduler.run_agent("unknown", context, "proj-1")

    @pytest.mark.asyncio
    async def test_schedule_agent_failure(self):
        llm_client = MagicMock()
        ws_manager = AsyncMock()
        state_store = MagicMock()

        scheduler = AgentScheduler(llm_client, ws_manager, state_store)

        mock_agent_class = MagicMock()
        mock_instance = mock_agent_class.return_value
        mock_instance.run = AsyncMock(side_effect=RuntimeError("LLM failed"))

        with patch.dict(
            "backend.orchestrator.scheduler.AGENT_MAP", {"pm": mock_agent_class}, clear=False
        ):
            context = AgentContext(requirement="build a thing", project_id="proj-1")
            with pytest.raises(RuntimeError, match="LLM failed"):
                await scheduler.run_agent("pm", context, "proj-1")

            # Verify failure notification was sent
            assert ws_manager.send_message.await_count == 2
            call_2 = ws_manager.send_message.await_args_list[1]
            assert call_2[0][1]["status"] == "failed"
            assert call_2[0][1]["error"] == "LLM failed"
