"""Tests for CoderAgent."""

import pytest
from unittest.mock import AsyncMock, patch

from backend.agents.base_agent import AgentContext
from backend.agents.coder_agent import CoderAgent
from backend.llm.client import LLMClient


@pytest.fixture
def llm_client():
    return LLMClient(anthropic_key="test-key", openai_key="test-key")


@pytest.mark.asyncio
async def test_coder_agent_generates_code(llm_client):
    """Test that CoderAgent parses FILE blocks correctly from LLM response."""
    agent = CoderAgent(llm_client=llm_client)
    context = AgentContext(
        requirement="Build a todo app",
        project_id="proj-123",
        spec="# Spec\n\nTodo app spec",
        architecture="# Architecture\n\nThree-layer architecture",
    )

    mock_response = """### FILE: app/main.py
```python
def main():
    print("Hello")
```

### FILE: app/models.py
```python
class Todo:
    pass
```
"""

    with patch.object(agent, "_call_llm", new_callable=AsyncMock) as mock_call_llm:
        mock_call_llm.return_value = mock_response
        result = await agent.run(context)

    assert result.content == mock_response
    assert "app/main.py" in result.files
    assert "app/models.py" in result.files
    assert result.files["app/main.py"] == 'def main():\n    print("Hello")\n'
    assert result.files["app/models.py"] == 'class Todo:\n    pass\n'
    assert result.metadata["agent_type"] == "coder"
    assert result.metadata["project_id"] == "proj-123"
    assert result.metadata["iteration"] == 0
    assert result.metadata["file_count"] == 2

    # Verify the LLM was called with correct arguments
    mock_call_llm.assert_called_once()
    call_args = mock_call_llm.call_args
    assert call_args.kwargs["temperature"] == 0.3


@pytest.mark.asyncio
async def test_coder_agent_with_review_feedback(llm_client):
    """Test that CoderAgent includes review feedback in the prompt."""
    agent = CoderAgent(llm_client=llm_client)
    context = AgentContext(
        requirement="Build a todo app",
        project_id="proj-123",
        spec="# Spec\n\nTodo app spec",
        architecture="# Architecture\n\nThree-layer architecture",
        review_feedback="Add error handling to the main function.",
        iteration=1,
    )

    mock_response = """### FILE: app/main.py
```python
def main():
    try:
        print("Hello")
    except Exception:
        pass
```
"""

    with patch.object(agent, "_call_llm", new_callable=AsyncMock) as mock_call_llm:
        mock_call_llm.return_value = mock_response
        result = await agent.run(context)

    # Verify review feedback was included in the LLM call
    mock_call_llm.assert_called_once()
    call_args = mock_call_llm.call_args
    user_prompt = call_args.kwargs["user_prompt"]
    assert "Add error handling to the main function." in user_prompt
    assert "Iteration: 1" in user_prompt
    assert result.metadata["iteration"] == 1
