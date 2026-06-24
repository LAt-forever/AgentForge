"""Product Manager Agent implementation."""

from backend.agents.base_agent import AgentContext, AgentOutput, BaseAgent
from backend.llm.client import LLMClient


class PMAgent(BaseAgent):
    """Agent that analyzes user requirements and produces a structured functional specification."""

    def __init__(self, llm_client: LLMClient):
        super().__init__(name="pm", llm_client=llm_client)

    async def run(self, context: AgentContext) -> AgentOutput:
        """Analyze requirement and produce a structured functional specification."""
        system_prompt = self._load_prompt("pm")
        user_prompt_parts = []
        if context.workflow_prompt_context:
            user_prompt_parts.append(f"Workflow Context:\n{context.workflow_prompt_context}")
        user_prompt_parts.append(f"User Requirement:\n{context.requirement}")
        user_prompt_parts.append(
            "Please analyze and produce a structured functional specification."
        )
        user_prompt = "\n\n".join(user_prompt_parts)

        spec = await self._call_llm(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.5,
        )

        return AgentOutput(
            content=spec,
            metadata={
                "agent_type": "pm",
                "project_id": context.project_id,
            },
        )
