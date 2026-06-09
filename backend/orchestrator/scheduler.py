"""Agent scheduler for running agents and notifying status."""

from backend.agents.architect_agent import ArchitectAgent
from backend.agents.base_agent import AgentContext, AgentOutput
from backend.agents.coder_agent import CoderAgent
from backend.agents.pm_agent import PMAgent
from backend.agents.reviewer_agent import ReviewerAgent
from backend.llm.client import LLMClient


AGENT_MAP = {
    "pm": PMAgent,
    "architect": ArchitectAgent,
    "coder": CoderAgent,
    "reviewer": ReviewerAgent,
}


class AgentScheduler:
    """Schedules agent execution and broadcasts status updates."""

    def __init__(self, llm_client: LLMClient, ws_manager, state_store):
        self.llm_client = llm_client
        self.ws_manager = ws_manager
        self.state_store = state_store

    async def run_agent(self, agent_name: str, context: AgentContext, project_id: str):
        """Run an agent and notify status throughout execution.

        Args:
            agent_name: Name of the agent to run (pm, architect, coder, reviewer).
            context: Execution context for the agent.
            project_id: Project ID for status notifications.

        Returns:
            The AgentOutput from the agent's run() method.

        Raises:
            ValueError: If the agent name is unknown.
        """
        agent_class = AGENT_MAP.get(agent_name)
        if agent_class is None:
            raise ValueError(f"Unknown agent: {agent_name}")

        agent = agent_class(self.llm_client)

        await self._notify_status(project_id, agent_name, "running")

        try:
            result = await agent.run(context)
        except Exception as exc:
            await self._notify_status(
                project_id, agent_name, "failed", error=str(exc)
            )
            raise

        await self._notify_status(project_id, agent_name, "completed", result)
        return result

    async def _notify_status(
        self, project_id, agent_name, status, output=None, error=None
    ):
        """Send a status notification via WebSocket and update state store."""
        message = {
            "type": "agent_status",
            "project_id": project_id,
            "agent": agent_name,
            "status": status,
        }

        if output is not None:
            summary = output.content[:200] if len(output.content) > 200 else output.content
            message["output"] = {
                "summary": summary,
                "files": list(output.files.keys()),
                "metadata": output.metadata,
            }

        if error is not None:
            message["error"] = error

        await self.ws_manager.send_message(project_id, message)

        # Update state store
        self.state_store.update_agent_status(
            project_id,
            agent_name,
            {"status": status, "output": message.get("output"), "error": error},
        )
