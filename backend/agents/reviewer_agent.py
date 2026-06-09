"""Reviewer Agent implementation."""

import json
import re

from backend.agents.base_agent import AgentContext, AgentOutput, BaseAgent
from backend.llm.client import LLMClient


class ReviewerAgent(BaseAgent):
    """Agent that reviews code against spec and architecture."""

    def __init__(self, llm_client: LLMClient):
        super().__init__(name="reviewer", llm_client=llm_client)

    async def run(self, context: AgentContext) -> AgentOutput:
        """Review code against spec and architecture."""
        system_prompt = self._load_prompt("reviewer")

        code_sections = []
        for filepath, content in context.code.items():
            code_sections.append(f"### {filepath}\n```\n{content}\n```")
        code_text = "\n\n".join(code_sections)

        user_prompt = (
            f"Functional Specification:\n{context.spec}\n\n"
            f"Architecture:\n{context.architecture}\n\n"
            f"Code Files:\n{code_text}"
        )

        review_response = await self._call_llm(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.3,
        )

        review_data = self._parse_review(review_response)

        return AgentOutput(
            content=review_response,
            metadata={
                "agent_type": "reviewer",
                "project_id": context.project_id,
                "passed": review_data.get("passed", False),
                "issues": review_data.get("issues", []),
                "summary": review_data.get("summary", ""),
            },
        )

    def _parse_review(self, review_response: str) -> dict:
        """Parse JSON review from LLM response.

        Tries regex for code block first, then raw string.
        Falls back to a default error response on parse failure.
        """
        # Try to extract JSON from code block
        pattern = r'```(?:json)?\s*\n?(.*?)\n?```'
        match = re.search(pattern, review_response, re.DOTALL)

        if match:
            json_str = match.group(1).strip()
        else:
            # Try raw string
            json_str = review_response.strip()

        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            return {
                "passed": False,
                "issues": [
                    {
                        "severity": "warning",
                        "message": "Could not parse review JSON from LLM response.",
                    }
                ],
                "summary": "Review parsing failed",
            }
