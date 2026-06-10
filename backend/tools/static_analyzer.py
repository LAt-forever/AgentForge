"""Static analysis tools (pylint, mypy, tsc) run inside the sandbox."""

import json
import logging
import re
from dataclasses import dataclass

from backend.tools.docker_sandbox import DockerSandbox

logger = logging.getLogger(__name__)


@dataclass
class Issue:
    """A single static-analysis finding."""

    tool: str
    file: str
    line: int
    column: int
    severity: str  # "error" | "warning" | "info"
    message: str
    code: str | None = None


# pylint type -> our severity
_PYLINT_SEVERITY = {
    "error": "error",
    "fatal": "error",
    "warning": "warning",
    "refactor": "info",
    "convention": "info",
    "info": "info",
}

_MYPY_LINE = re.compile(
    r"^(?P<file>[^:]+):(?P<line>\d+):(?:(?P<col>\d+):)?\s*"
    r"(?P<severity>error|warning|note):\s*(?P<msg>.*?)(?:\s+\[(?P<code>[^\]]+)\])?$"
)


class StaticAnalyzer:
    """Runs static analysis inside a DockerSandbox and returns structured issues."""

    def __init__(self, sandbox: DockerSandbox):
        self.sandbox = sandbox

    def analyze(self, project_id: str, language: str, files: list[str]) -> list[Issue]:
        """Dispatch to the right analyzer by language."""
        if language == "python":
            py_files = [f for f in files if f.endswith(".py")]
            return self.analyze_python(project_id, py_files)
        if language in ("typescript", "javascript"):
            ts_files = [f for f in files if f.endswith((".ts", ".tsx", ".js"))]
            return self.analyze_typescript(project_id, ts_files)
        return []

    def analyze_python(self, project_id: str, files: list[str]) -> list[Issue]:
        """Run pylint + mypy on the given python files."""
        if not files:
            return []
        issues: list[Issue] = []
        issues.extend(self._run_pylint(project_id, files))
        issues.extend(self._run_mypy(project_id, files))
        return issues

    def analyze_typescript(self, project_id: str, files: list[str]) -> list[Issue]:
        """Run tsc --noEmit on the given TS/JS files."""
        if not files:
            return []
        result = self.sandbox.execute(
            project_id,
            ["npx", "tsc", "--noEmit", "--pretty", "false"] + files,
            timeout=60,
        )
        return self._parse_tsc(result.stdout + result.stderr)

    def _run_pylint(self, project_id: str, files: list[str]) -> list[Issue]:
        result = self.sandbox.execute(
            project_id, ["pylint", "--output-format=json"] + files, timeout=60
        )
        try:
            records = json.loads(result.stdout) if result.stdout.strip() else []
        except json.JSONDecodeError:
            logger.warning("Could not parse pylint output for %s", project_id)
            return []
        issues = []
        for r in records:
            issues.append(
                Issue(
                    tool="pylint",
                    file=r.get("path", ""),
                    line=r.get("line", 0),
                    column=r.get("column", 0),
                    severity=_PYLINT_SEVERITY.get(r.get("type", ""), "info"),
                    message=r.get("message", ""),
                    code=r.get("message-id"),
                )
            )
        return issues

    def _run_mypy(self, project_id: str, files: list[str]) -> list[Issue]:
        result = self.sandbox.execute(
            project_id,
            ["mypy", "--no-error-summary", "--no-color-output"] + files,
            timeout=60,
        )
        issues = []
        for line in (result.stdout + result.stderr).splitlines():
            m = _MYPY_LINE.match(line.strip())
            if not m:
                continue
            sev = m.group("severity")
            if sev == "note":
                sev = "info"
            issues.append(
                Issue(
                    tool="mypy",
                    file=m.group("file"),
                    line=int(m.group("line")),
                    column=int(m.group("col") or 0),
                    severity=sev,
                    message=m.group("msg"),
                    code=m.group("code"),
                )
            )
        return issues

    def _parse_tsc(self, output: str) -> list[Issue]:
        # tsc format: file.ts(12,5): error TS2304: Cannot find name 'foo'.
        pattern = re.compile(
            r"^(?P<file>[^(]+)\((?P<line>\d+),(?P<col>\d+)\):\s+"
            r"(?P<severity>error|warning)\s+(?P<code>TS\d+):\s+(?P<msg>.*)$"
        )
        issues = []
        for line in output.splitlines():
            m = pattern.match(line.strip())
            if not m:
                continue
            issues.append(
                Issue(
                    tool="tsc",
                    file=m.group("file"),
                    line=int(m.group("line")),
                    column=int(m.group("col")),
                    severity=m.group("severity"),
                    message=m.group("msg"),
                    code=m.group("code"),
                )
            )
        return issues
