"""Reviewer Agent implementation."""

import json
import os
import re

from backend.agents.base_agent import AgentContext, AgentOutput, BaseAgent
from backend.config import settings
from backend.llm.client import LLMClient
from backend.tools.file_manager import FileManager
from backend.tools.docker_sandbox import DockerSandbox
from backend.tools.static_analyzer import StaticAnalyzer


class ReviewerAgent(BaseAgent):
    """Agent that reviews code against spec and architecture."""

    def __init__(self, llm_client: LLMClient):
        super().__init__(name="reviewer", llm_client=llm_client)

    async def run(self, context: AgentContext) -> AgentOutput:
        """Review code against spec and architecture.

        Reads actual files from disk instead of relying on context.code
        to avoid false negatives when Coder's parser is imperfect.
        """
        system_prompt = self._load_prompt("reviewer")

        # Read actual files from disk
        project_dir = os.path.join(settings.output_dir, context.project_id)
        fm = FileManager(base_dir=project_dir)
        actual_files = fm.list_files()

        # Filter to code files + requirements/spec for context
        code_extensions = (
            ".py", ".js", ".ts", ".go", ".rs", ".java", ".cpp", ".c", ".h", ".html", ".css"
        )
        review_files = [
            f for f in actual_files
            if f.endswith(code_extensions) or f in ("requirements.txt", "README.md")
        ]

        code_sections = []
        for filepath in review_files:
            try:
                content = fm.read_file(filepath)
                # Skip very short or metadata-only files
                if len(content.strip()) < 5:
                    continue
                code_sections.append(f"### {filepath}\n```\n{content}\n```")
            except Exception:
                continue

        if not code_sections:
            # No actual code files on disk - this is a real failure
            return AgentOutput(
                content=json.dumps({
                    "passed": False,
                    "issues": [{
                        "severity": "error",
                        "message": "No code files were found in the project directory.",
                        "suggestion": "Generate the implementation files before review.",
                    }],
                    "summary": "No code files available for review.",
                }),
                metadata={
                    "agent_type": "reviewer",
                    "project_id": context.project_id,
                    "passed": False,
                    "issues": [{
                        "severity": "error",
                        "message": "No code files were found in the project directory.",
                    }],
                    "summary": "No code files available for review.",
                },
            )

        code_text = "\n\n".join(code_sections)

        analysis_section = self._run_static_analysis(context.project_id, review_files)

        user_prompt_parts = []
        if context.workflow_prompt_context:
            user_prompt_parts.append(f"Workflow Context:\n{context.workflow_prompt_context}")
        user_prompt_parts.extend([
            f"Functional Specification:\n{context.spec}",
            f"Architecture:\n{context.architecture}",
            f"Code Files:\n{code_text}{analysis_section}",
            (
                "Important: Code files ARE provided above. Do NOT say 'no code files "
                "provided'. Review the actual code for completeness, correctness, and quality."
            ),
        ])
        user_prompt = "\n\n".join(user_prompt_parts)

        review_response = await self._call_llm(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.3,
        )

        review_data = self._parse_review(review_response)

        # Post-process: override false negatives
        if actual_files and not review_data.get("passed", False):
            issues = review_data.get("issues", [])
            filtered_issues = [
                issue for issue in issues
                if "no code" not in issue.get("message", "").lower()
                and "no source" not in issue.get("message", "").lower()
                and "no application" not in issue.get("message", "").lower()
            ]
            if len(filtered_issues) != len(issues):
                review_data["issues"] = filtered_issues
                # Re-evaluate pass criteria after filtering false negatives
                has_errors = any(
                    issue.get("severity") == "error" for issue in filtered_issues
                )
                review_data["passed"] = not has_errors

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

    def _run_static_analysis(self, project_id: str, files: list[str]) -> str:
        """Run static analysis when the sandbox is enabled; return a prompt section.

        Returns an empty string when the sandbox is off or no issues are found.
        Any tool/sandbox failure is swallowed so review never breaks.
        """
        if not settings.use_docker_sandbox:
            return ""
        language = getattr(settings, "default_language", "python")
        try:
            sandbox = DockerSandbox(
                container_name=settings.sandbox_container_name,
                image=settings.sandbox_image,
            )
            analyzer = StaticAnalyzer(sandbox)
            issues = analyzer.analyze(project_id, language, files)
        except Exception:  # noqa: BLE001 - tool failures must not break review
            return ""
        if not issues:
            return ""
        lines = [
            f"- [{i.tool}:{i.severity}] {i.file}:{i.line} {i.message}"
            f"{f' ({i.code})' if i.code else ''}"
            for i in issues
        ]
        return (
            "\n\nStatic analysis tools reported the following findings. "
            "Consider them alongside your own judgment:\n" + "\n".join(lines)
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
