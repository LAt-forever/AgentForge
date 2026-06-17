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
        language = context.language or "python"
        user_prompt_parts = [
            f"Target language: {language}. Generate all code in {language}.",
            f"IMPORTANT: The entry-point file (e.g. main.py, app.py, index.ts) must be directly executable. "
            f"Do NOT use relative imports (e.g. `from .config import ...`) in the entry-point file. "
            f"Use inline constants, absolute imports, or `sys.path` manipulation instead.",
        ]
        if context.workflow_prompt_context:
            user_prompt_parts.append(
                f"Workflow Context:\n{context.workflow_prompt_context}"
            )
        user_prompt_parts.extend([
            f"Functional Specification:\n{context.spec}",
            f"\nArchitecture:\n{context.architecture}",
        ])

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

        Supports multiple output formats from different LLMs:
        - ### FILE: <filepath>\n```<lang>\n<content>```
        - ### FILE: <filepath>\n```\n<content>```
        - ```<lang>:<filepath>\n<content>```
        - Filename as markdown heading + code block
        """
        files = {}

        # Pattern 1: ### FILE: filepath followed by ``` or ```lang
        # Allow optional blank lines between FILE and code block
        pattern1 = r'###\s*FILE:\s*([^\n]+)(?:\n+|\r?\n)```(?:\w+)?\n(.*?)```'
        matches = list(re.finditer(pattern1, code_response, re.DOTALL))

        if matches:
            for match in matches:
                filepath = match.group(1).strip().strip('`')
                content = match.group(2).rstrip()
                if filepath and content:
                    files[filepath] = content
            return files

        # Pattern 2: filename on its own line before code block
        # e.g. "hello_world.py\n```python\n...\n```"
        pattern2 = r'^([\w./_-]+\.pyw?)$\r?\n```(?:\w+)?\n(.*?)```'
        matches = list(re.finditer(pattern2, code_response, re.MULTILINE | re.DOTALL))
        if matches:
            for match in matches:
                filepath = match.group(1).strip()
                content = match.group(2).rstrip()
                if filepath and content:
                    files[filepath] = content
            return files

        # Pattern 3: code blocks with filepath in language tag
        # e.g. ```python:hello_world.py\n...\n```
        pattern3 = r'```\w+:(\S+)\n(.*?)```'
        matches = list(re.finditer(pattern3, code_response, re.DOTALL))
        if matches:
            for match in matches:
                filepath = match.group(1).strip()
                content = match.group(2).rstrip()
                if filepath and content:
                    files[filepath] = content
            return files

        # Pattern 4: just code blocks - try to infer filenames
        pattern4 = r'```(?:\w+)?\n(.*?)```'
        matches = list(re.finditer(pattern4, code_response, re.DOTALL))
        for i, match in enumerate(matches, start=1):
            content = match.group(1)
            # Look for a filename in the 3 lines before this code block
            block_start = match.start()
            preceding = code_response[max(0, block_start - 500):block_start]
            filename_match = re.search(r'([\w_-]+\.pyw?)[\s`]*$', preceding, re.MULTILINE)
            if filename_match:
                filepath = filename_match.group(1).strip()
            else:
                filepath = f"file_{i}.py"
            files[filepath] = content.rstrip()

        return files
