"""Tests for BaseAgent."""

import pytest

from backend.agents.base_agent import AgentContext, AgentOutput, BaseAgent
from backend.llm.client import LLMClient


class DummyAgent(BaseAgent):
    """Concrete agent for testing."""

    async def run(self, context: AgentContext) -> AgentOutput:
        return AgentOutput(
            content=f"Hello from {self.name}",
            files={"test.py": "print('hello')"},
            metadata={"agent": self.name},
        )


@pytest.fixture
def llm_client():
    return LLMClient(anthropic_key="test-key", openai_key="test-key")


@pytest.mark.asyncio
async def test_base_agent_run(llm_client):
    """Test that run() returns expected AgentOutput."""
    agent = DummyAgent(name="test-agent", llm_client=llm_client)
    context = AgentContext(
        requirement="Build a calculator",
        project_id="proj-123",
    )
    result = await agent.run(context)

    assert isinstance(result, AgentOutput)
    assert result.content == "Hello from test-agent"
    assert result.files == {"test.py": "print('hello')"}
    assert result.metadata == {"agent": "test-agent"}


def test_base_agent_name(llm_client):
    """Test that the agent name is set correctly."""
    agent = DummyAgent(name="my-agent", llm_client=llm_client)
    assert agent.name == "my-agent"
