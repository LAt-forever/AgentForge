"""Tests for PMAgent."""

import pytest
from unittest.mock import AsyncMock, patch

from backend.agents.base_agent import AgentContext
from backend.agents.pm_agent import PMAgent
from backend.llm.client import LLMClient


@pytest.fixture
def llm_client():
    return LLMClient(anthropic_key="test-key", openai_key="test-key")


@pytest.mark.asyncio
async def test_pm_agent_generates_spec(llm_client):
    """Test that PMAgent generates a spec containing 'Overview'."""
    agent = PMAgent(llm_client=llm_client)
    context = AgentContext(
        requirement="Build a todo app",
        project_id="proj-123",
    )

    mock_response = "# Overview\n\nThis is a todo app.\n\n## User Stories\n\n- As a user..."

    with patch.object(agent, "_call_llm", new_callable=AsyncMock) as mock_call_llm:
        mock_call_llm.return_value = mock_response
        result = await agent.run(context)

    assert "Overview" in result.content
    assert result.metadata["agent_type"] == "pm"
    assert result.metadata["project_id"] == "proj-123"

    # Verify the LLM was called with correct arguments
    mock_call_llm.assert_called_once()
    call_args = mock_call_llm.call_args
    assert call_args.kwargs["temperature"] == 0.5
    assert "Build a todo app" in call_args.kwargs["user_prompt"]
