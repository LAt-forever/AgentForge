"""Architect Agent implementation."""

from backend.agents.base_agent import AgentContext, AgentOutput, BaseAgent
from backend.llm.client import LLMClient


class ArchitectAgent(BaseAgent):
    """Agent that produces a system architecture design from a functional specification."""

    def __init__(self, llm_client: LLMClient):
        super().__init__(name="architect", llm_client=llm_client)

    async def run(self, context: AgentContext) -> AgentOutput:
        """Generate system architecture from the functional specification."""
        system_prompt = self._load_prompt("architect")
        user_prompt_parts = []
        if context.workflow_prompt_context:
            user_prompt_parts.append(f"Workflow Context:\n{context.workflow_prompt_context}")
        user_prompt_parts.append(f"Functional Specification:\n{context.spec}")
        user_prompt = "\n\n".join(user_prompt_parts)

        architecture = await self._call_llm(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.4,
        )

        return AgentOutput(
            content=architecture,
            metadata={
                "agent_type": "architect",
                "project_id": context.project_id,
            },
        )
