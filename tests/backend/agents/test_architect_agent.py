"""Tests for ArchitectAgent."""

import pytest
from unittest.mock import AsyncMock, patch

from backend.agents.base_agent import AgentContext
from backend.agents.architect_agent import ArchitectAgent
from backend.llm.client import LLMClient


@pytest.fixture
def llm_client():
    return LLMClient(anthropic_key="test-key", openai_key="test-key")


@pytest.mark.asyncio
async def test_architect_agent_generates_design(llm_client):
    """Test that ArchitectAgent generates an architecture containing 'Module Overview'."""
    agent = ArchitectAgent(llm_client=llm_client)
    context = AgentContext(
        requirement="Build a todo app",
        project_id="proj-123",
        spec="# Spec\n\nThis is a todo app spec.",
    )

    mock_response = "# Module Overview\n\nThe system has three modules...\n\n## Data Model\n\n..."

    with patch.object(agent, "_call_llm", new_callable=AsyncMock) as mock_call_llm:
        mock_call_llm.return_value = mock_response
        result = await agent.run(context)

    assert "Module Overview" in result.content
    assert result.metadata["agent_type"] == "architect"
    assert result.metadata["project_id"] == "proj-123"

    # Verify the LLM was called with correct arguments
    mock_call_llm.assert_called_once()
    call_args = mock_call_llm.call_args
    assert call_args.kwargs["temperature"] == 0.4
    assert "# Spec" in call_args.kwargs["user_prompt"]
