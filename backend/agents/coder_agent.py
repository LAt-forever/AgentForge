"""Coder Agent implementation."""

import re

from backend.agents.base_agent import AgentContext, AgentOutput, BaseAgent
from backend.llm.client import LLMClient


class CoderAgent(BaseAgent):
    """Agent that generates code from specification and architecture."""

    def __init__(self, llm_client: LLMClient):
        super().__init__(name="coder", llm_client=llm_client)

    async def run(self, context: AgentContext) -> AgentOutput:
        """Generate code from spec and architecture."""
        system_prompt = self._load_prompt("coder")
        user_prompt_parts = [
            f"Functional Specification:\n{context.spec}",
            f"\nArchitecture:\n{context.architecture}",
        ]

        if context.review_feedback:
            user_prompt_parts.append(
                f"\nReview Feedback:\n{context.review_feedback}"
            )

        if context.iteration > 0:
            user_prompt_parts.append(
                f"\nIteration: {context.iteration}"
            )

        user_prompt = "\n".join(user_prompt_parts)

        code_response = await self._call_llm(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.3,
        )

        files = self._parse_files(code_response)

        return AgentOutput(
            content=code_response,
            files=files,
            metadata={
                "agent_type": "coder",
                "project_id": context.project_id,
                "iteration": context.iteration,
                "file_count": len(files),
            },
        )

    def _parse_files(self, code_response: str) -> dict:
        """Parse code files from LLM response.

        Pattern: ### FILE: <filepath>\n```<lang>\n<content>```
        Fallback: ```<lang>\n<content>``` named as file_1.py, file_2.py, etc.
        """
        files = {}

        # Primary pattern: ### FILE: filepath
        pattern = r'###\s*FILE:\s*([^\n]+)\n```(?:\w+)?\n(.*?)```'
        matches = list(re.finditer(pattern, code_response, re.DOTALL))

        if matches:
            for match in matches:
                filepath = match.group(1).strip()
                content = match.group(2)
                files[filepath] = content
        else:
            # Fallback pattern: just code blocks without FILE markers
            fallback_pattern = r'```(?:\w+)?\n(.*?)```'
            fallback_matches = list(
                re.finditer(fallback_pattern, code_response, re.DOTALL)
            )
            for i, match in enumerate(fallback_matches, start=1):
                content = match.group(1)
                files[f"file_{i}.py"] = content

        return files
