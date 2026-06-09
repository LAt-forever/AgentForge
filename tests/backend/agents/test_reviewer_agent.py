"""Tests for ReviewerAgent."""

import pytest
from unittest.mock import AsyncMock, patch

from backend.agents.base_agent import AgentContext
from backend.agents.reviewer_agent import ReviewerAgent
from backend.llm.client import LLMClient


@pytest.fixture
def llm_client():
    return LLMClient(anthropic_key="test-key", openai_key="test-key")


@pytest.mark.asyncio
async def test_reviewer_agent_with_issues(llm_client):
    """Test that ReviewerAgent parses JSON review with issues correctly."""
    agent = ReviewerAgent(llm_client=llm_client)
    context = AgentContext(
        requirement="Build a todo app",
        project_id="proj-123",
        spec="# Spec\n\nTodo app spec",
        architecture="# Architecture\n\nThree-layer architecture",
        code={
            "app/main.py": "def main():\n    print('hello')",
            "app/models.py": "class Todo:\n    pass",
        },
    )

    mock_response = """```json
{
    "passed": false,
    "issues": [
        {"severity": "error", "message": "Missing type hints in main.py"},
        {"severity": "warning", "message": "Todo class has no docstring"}
    ],
    "summary": "Code has 2 issues that need to be addressed."
}
```"""

    with patch.object(agent, "_call_llm", new_callable=AsyncMock) as mock_call_llm:
        mock_call_llm.return_value = mock_response
        result = await agent.run(context)

    assert result.metadata["agent_type"] == "reviewer"
    assert result.metadata["project_id"] == "proj-123"
    assert result.metadata["passed"] is False
    assert len(result.metadata["issues"]) == 2
    assert result.metadata["issues"][0]["severity"] == "error"
    assert result.metadata["summary"] == "Code has 2 issues that need to be addressed."

    # Verify the LLM was called with correct arguments
    mock_call_llm.assert_called_once()
    call_args = mock_call_llm.call_args
    assert call_args.kwargs["temperature"] == 0.3
    # Verify code files are included in the prompt
    user_prompt = call_args.kwargs["user_prompt"]
    assert "app/main.py" in user_prompt
    assert "app/models.py" in user_prompt


@pytest.mark.asyncio
async def test_reviewer_agent_passed(llm_client):
    """Test that ReviewerAgent parses JSON review with passed=true correctly."""
    agent = ReviewerAgent(llm_client=llm_client)
    context = AgentContext(
        requirement="Build a todo app",
        project_id="proj-123",
        spec="# Spec\n\nTodo app spec",
        architecture="# Architecture\n\nThree-layer architecture",
        code={
            "app/main.py": "def main():\n    print('hello')",
        },
    )

    mock_response = """```json
{
    "passed": true,
    "issues": [],
    "summary": "All code looks good. No issues found."
}
```"""

    with patch.object(agent, "_call_llm", new_callable=AsyncMock) as mock_call_llm:
        mock_call_llm.return_value = mock_response
        result = await agent.run(context)

    assert result.metadata["agent_type"] == "reviewer"
    assert result.metadata["project_id"] == "proj-123"
    assert result.metadata["passed"] is True
    assert result.metadata["issues"] == []
    assert result.metadata["summary"] == "All code looks good. No issues found."
