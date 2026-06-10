"""Tests for ReviewerAgent."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from backend.agents.base_agent import AgentContext
from backend.agents.reviewer_agent import ReviewerAgent
from backend.llm.client import LLMClient
from backend.tools.static_analyzer import Issue


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


@pytest.mark.asyncio
async def test_reviewer_includes_static_analysis_in_prompt(tmp_path, monkeypatch):
    """When sandbox is on, analyzer issues are injected into the reviewer prompt."""
    from backend.config import settings

    proj = tmp_path / "proj1"
    proj.mkdir()
    (proj / "main.py").write_text("x = 1\n")
    monkeypatch.setattr(settings, "output_dir", str(tmp_path))
    monkeypatch.setattr(settings, "use_docker_sandbox", True)

    agent = ReviewerAgent(llm_client=MagicMock())
    captured = {}

    async def fake_call(system_prompt, user_prompt, temperature=0.3):
        captured["user_prompt"] = user_prompt
        return '{"passed": true, "issues": [], "summary": "ok"}'

    agent._call_llm = fake_call

    fake_issue = Issue(
        tool="pylint", file="main.py", line=1, column=0,
        severity="warning", message="Constant name doesn't conform", code="C0103",
    )
    with patch("backend.agents.reviewer_agent.StaticAnalyzer") as MockAnalyzer:
        MockAnalyzer.return_value.analyze.return_value = [fake_issue]
        ctx = AgentContext(requirement="r", project_id="proj1", spec="s", architecture="a")
        await agent.run(ctx)

    assert "Static analysis" in captured["user_prompt"]
    assert "C0103" in captured["user_prompt"]


@pytest.mark.asyncio
async def test_reviewer_skips_analysis_when_sandbox_off(tmp_path, monkeypatch):
    """When sandbox is off, no analyzer call and prompt has no analysis section."""
    from backend.config import settings

    proj = tmp_path / "proj1"
    proj.mkdir()
    (proj / "main.py").write_text("x = 1\n")
    monkeypatch.setattr(settings, "output_dir", str(tmp_path))
    monkeypatch.setattr(settings, "use_docker_sandbox", False)

    agent = ReviewerAgent(llm_client=MagicMock())
    captured = {}

    async def fake_call(system_prompt, user_prompt, temperature=0.3):
        captured["user_prompt"] = user_prompt
        return '{"passed": true, "issues": [], "summary": "ok"}'

    agent._call_llm = fake_call

    with patch("backend.agents.reviewer_agent.StaticAnalyzer") as MockAnalyzer:
        ctx = AgentContext(requirement="r", project_id="proj1", spec="s", architecture="a")
        await agent.run(ctx)
        MockAnalyzer.assert_not_called()

    assert "Static analysis" not in captured["user_prompt"]
