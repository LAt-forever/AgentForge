# Phase 3: Capability Enhancement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Augment the Reviewer with pylint/mypy static analysis, enable multi-language (Python + TypeScript) code generation, and add a Settings panel with backend persistence for API keys, model, max iterations, timeout, target language, and Docker toggle.

**Architecture:** A `StaticAnalyzer` runs lint tools inside the Docker sandbox (falling back to no-op when the sandbox is off) and feeds structured `Issue`s into the Reviewer's prompt. `CoderAgent` injects an explicit language directive (no template engine — prompts are sent raw today). A `SettingsManager` persists JSON overrides on top of env defaults; new REST endpoints expose and update them, rebuilding the `LLMClient` on change.

**Tech Stack:** Python 3.11, FastAPI, pylint/mypy/eslint/tsc (in sandbox), React 18 + TypeScript, Zustand, Vite

**Key decisions (locked):**
- **No temperature control in Settings UI** — each agent uses a tuned temperature (PM 0.5, Architect 0.4, Coder/Reviewer 0.3); a single global override would degrade quality. (User-confirmed.)
- **No template engine** — multi-language is done by injecting a directive string in `CoderAgent`, matching the existing raw-prompt approach.
- Static analysis **augments** the LLM reviewer (results injected into the prompt); it does not replace the LLM's judgment.

**Verification note:** Frontend has no test runner — verify with `cd frontend && npm run build`. Backend: `PYTHONPATH=/Users/lanhezheng/vibe-agent pytest ...`. The 5 pre-existing agent/llm test failures are unrelated to this work; confirm no NEW failures.

---

## File Structure

| File | Action | Responsibility |
|------|--------|---------------|
| `backend/tools/static_analyzer.py` | Create | Run pylint/mypy (and tsc/eslint) in sandbox; parse to `Issue` list |
| `tests/backend/tools/test_static_analyzer.py` | Create | Unit tests (mocked sandbox) for parsing + dispatch |
| `backend/agents/reviewer_agent.py` | Modify | Run StaticAnalyzer, inject findings into prompt |
| `backend/agents/coder_agent.py` | Modify | Inject target-language directive into prompt |
| `tests/backend/agents/test_coder_agent.py` | Modify | Assert language directive present |
| `backend/config.py` | Modify | Add `default_language` |
| `backend/core/settings_manager.py` | Create | JSON overrides over env defaults; masked reads |
| `tests/backend/core/test_settings_manager.py` | Create | Unit tests for load/update/mask |
| `backend/main.py` | Modify | Settings endpoints + LLMClient rebuild + pass language to coder |
| `frontend/src/types/index.ts` | Modify | Add `AppSettings`, `ModelOption` types |
| `frontend/src/store/useStore.ts` | Modify | Add settings-panel open state |
| `frontend/src/components/SettingsPanel.tsx` | Create | Drawer: API keys, model, max iters, timeout, language, sandbox |
| `frontend/src/components/FileTree.tsx` | Modify | Distinct icons for `.ts`/`.tsx` vs `.js` |
| `frontend/src/components/Layout.tsx` | Modify | Settings gear button + mount SettingsPanel |

---

## Task 1: StaticAnalyzer — Issue model + Python analysis

**Files:**
- Create: `backend/tools/static_analyzer.py`
- Create: `tests/backend/tools/test_static_analyzer.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/backend/tools/test_static_analyzer.py
"""Tests for StaticAnalyzer."""

from unittest.mock import MagicMock

import pytest

from backend.tools.static_analyzer import StaticAnalyzer, Issue
from backend.tools.docker_sandbox import ExecutionResult


class TestIssueModel:
    def test_issue_fields(self):
        issue = Issue(
            tool="pylint", file="main.py", line=10, column=4,
            severity="error", message="undefined name", code="E0602",
        )
        assert issue.tool == "pylint"
        assert issue.line == 10
        assert issue.severity == "error"


class TestAnalyzePython:
    def test_parses_pylint_json(self):
        """pylint JSON output is parsed into Issues."""
        sandbox = MagicMock()
        # pylint --output-format=json emits a JSON array
        pylint_json = (
            '[{"type":"error","module":"main","obj":"","line":3,"column":0,'
            '"path":"main.py","symbol":"undefined-variable",'
            '"message":"Undefined variable x","message-id":"E0602"}]'
        )
        # mypy returns no issues (exit 0, empty)
        sandbox.execute.side_effect = [
            ExecutionResult(stdout=pylint_json, stderr="", exit_code=1),
            ExecutionResult(stdout="", stderr="", exit_code=0),
        ]
        analyzer = StaticAnalyzer(sandbox)
        issues = analyzer.analyze_python("proj1", ["main.py"])

        pylint_issues = [i for i in issues if i.tool == "pylint"]
        assert len(pylint_issues) == 1
        assert pylint_issues[0].severity == "error"
        assert pylint_issues[0].line == 3
        assert pylint_issues[0].code == "E0602"

    def test_parses_mypy_output(self):
        """mypy text output is parsed into Issues."""
        sandbox = MagicMock()
        mypy_out = "main.py:5:1: error: Name 'foo' is not defined  [name-defined]\n"
        sandbox.execute.side_effect = [
            ExecutionResult(stdout="[]", stderr="", exit_code=0),  # pylint clean
            ExecutionResult(stdout=mypy_out, stderr="", exit_code=1),  # mypy
        ]
        analyzer = StaticAnalyzer(sandbox)
        issues = analyzer.analyze_python("proj1", ["main.py"])

        mypy_issues = [i for i in issues if i.tool == "mypy"]
        assert len(mypy_issues) == 1
        assert mypy_issues[0].line == 5
        assert mypy_issues[0].severity == "error"

    def test_no_files_returns_empty(self):
        """No python files → no analysis, empty list."""
        sandbox = MagicMock()
        analyzer = StaticAnalyzer(sandbox)
        assert analyzer.analyze_python("proj1", []) == []
        sandbox.execute.assert_not_called()

    def test_malformed_pylint_output_is_safe(self):
        """Garbage pylint output does not crash; yields no pylint issues."""
        sandbox = MagicMock()
        sandbox.execute.side_effect = [
            ExecutionResult(stdout="not json", stderr="", exit_code=1),
            ExecutionResult(stdout="", stderr="", exit_code=0),
        ]
        analyzer = StaticAnalyzer(sandbox)
        issues = analyzer.analyze_python("proj1", ["main.py"])
        assert [i for i in issues if i.tool == "pylint"] == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=/Users/lanhezheng/vibe-agent pytest tests/backend/tools/test_static_analyzer.py -v`
Expected: FAIL with ImportError (StaticAnalyzer, Issue not defined)

- [ ] **Step 3: Write minimal implementation**

```python
# backend/tools/static_analyzer.py
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
            project_id, ["npx", "tsc", "--noEmit", "--pretty", "false"] + files, timeout=60
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
            project_id, ["mypy", "--no-error-summary", "--no-color-output"] + files, timeout=60
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `PYTHONPATH=/Users/lanhezheng/vibe-agent pytest tests/backend/tools/test_static_analyzer.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add backend/tools/static_analyzer.py tests/backend/tools/test_static_analyzer.py
git commit -m "feat: add StaticAnalyzer for pylint/mypy/tsc in sandbox"
```

---

## Task 2: TypeScript analysis test

**Files:**
- Modify: `tests/backend/tools/test_static_analyzer.py`

- [ ] **Step 1: Append failing test**

```python
# tests/backend/tools/test_static_analyzer.py (append)

class TestAnalyzeTypeScript:
    def test_parses_tsc_output(self):
        """tsc error output is parsed into Issues."""
        sandbox = MagicMock()
        tsc_out = "main.ts(12,5): error TS2304: Cannot find name 'foo'.\n"
        sandbox.execute.return_value = ExecutionResult(
            stdout=tsc_out, stderr="", exit_code=2,
        )
        analyzer = StaticAnalyzer(sandbox)
        issues = analyzer.analyze_typescript("proj1", ["main.ts"])

        assert len(issues) == 1
        assert issues[0].tool == "tsc"
        assert issues[0].line == 12
        assert issues[0].column == 5
        assert issues[0].code == "TS2304"
        assert issues[0].severity == "error"

    def test_no_ts_files_returns_empty(self):
        sandbox = MagicMock()
        analyzer = StaticAnalyzer(sandbox)
        assert analyzer.analyze_typescript("proj1", []) == []
        sandbox.execute.assert_not_called()


class TestAnalyzeDispatch:
    def test_dispatch_python(self):
        sandbox = MagicMock()
        sandbox.execute.side_effect = [
            ExecutionResult(stdout="[]", stderr="", exit_code=0),
            ExecutionResult(stdout="", stderr="", exit_code=0),
        ]
        analyzer = StaticAnalyzer(sandbox)
        analyzer.analyze("p", "python", ["a.py", "b.ts"])
        # Only the .py file should be passed to pylint
        first_call_args = sandbox.execute.call_args_list[0][0][1]
        assert "a.py" in first_call_args
        assert "b.ts" not in first_call_args

    def test_dispatch_unknown_language(self):
        sandbox = MagicMock()
        analyzer = StaticAnalyzer(sandbox)
        assert analyzer.analyze("p", "rust", ["main.rs"]) == []
        sandbox.execute.assert_not_called()
```

- [ ] **Step 2: Run tests**

Run: `PYTHONPATH=/Users/lanhezheng/vibe-agent pytest tests/backend/tools/test_static_analyzer.py -v`
Expected: All PASS

- [ ] **Step 3: Commit**

```bash
git add tests/backend/tools/test_static_analyzer.py
git commit -m "test: add StaticAnalyzer TypeScript + dispatch coverage"
```

---

## Task 3: Reviewer integrates static analysis

**Files:**
- Modify: `backend/agents/reviewer_agent.py`
- Modify: `tests/backend/agents/test_reviewer_agent.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/backend/agents/test_reviewer_agent.py` (it already constructs a ReviewerAgent with a mocked LLM and a temp project dir — match that fixture style; read the file first to reuse its existing setup):

```python
# tests/backend/agents/test_reviewer_agent.py (append)

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from backend.tools.static_analyzer import Issue


@pytest.mark.asyncio
async def test_reviewer_includes_static_analysis_in_prompt(tmp_path, monkeypatch):
    """When sandbox is on, analyzer issues are injected into the reviewer prompt."""
    from backend.agents.base_agent import AgentContext
    from backend.agents.reviewer_agent import ReviewerAgent
    from backend.config import settings

    # Point output_dir at temp and create a code file
    proj = tmp_path / "proj1"
    proj.mkdir()
    (proj / "main.py").write_text("x = 1\n")
    monkeypatch.setattr(settings, "output_dir", str(tmp_path))
    monkeypatch.setattr(settings, "use_docker_sandbox", True)

    llm = MagicMock()
    agent = ReviewerAgent(llm_client=llm)

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
    from backend.agents.base_agent import AgentContext
    from backend.agents.reviewer_agent import ReviewerAgent
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=/Users/lanhezheng/vibe-agent pytest tests/backend/agents/test_reviewer_agent.py -k "static_analysis or sandbox_off" -v`
Expected: FAIL (analyzer not wired in)

- [ ] **Step 3: Write minimal implementation**

In `backend/agents/reviewer_agent.py`, add imports near the top:

```python
from backend.tools.docker_sandbox import DockerSandbox
from backend.tools.static_analyzer import StaticAnalyzer
```

Add a helper method to format issues (inside the `ReviewerAgent` class):

```python
    def _run_static_analysis(self, project_id: str, files: list[str]) -> str:
        """Run static analysis when the sandbox is enabled; return a prompt section.

        Returns an empty string when the sandbox is off or no issues are found.
        """
        if not settings.use_docker_sandbox:
            return ""
        # Default to python; multi-language detection can refine later.
        language = getattr(settings, "default_language", "python")
        try:
            sandbox = DockerSandbox(
                container_name=settings.sandbox_container_name,
                image=settings.sandbox_image,
            )
            analyzer = StaticAnalyzer(sandbox)
            issues = analyzer.analyze(project_id, language, files)
        except Exception:  # sandbox/tool failure must not break review
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
```

Then, in `run()`, after `code_text = "\n\n".join(code_sections)` and before building `user_prompt`, add:

```python
        analysis_section = self._run_static_analysis(context.project_id, review_files)
```

And append `analysis_section` to the `user_prompt` string (add it just before the final "Important:" sentence):

```python
        user_prompt = (
            f"Functional Specification:\n{context.spec}\n\n"
            f"Architecture:\n{context.architecture}\n\n"
            f"Code Files:\n{code_text}"
            f"{analysis_section}\n\n"
            f"Important: Code files ARE provided above. Do NOT say 'no code files provided'. "
            f"Review the actual code for completeness, correctness, and quality."
        )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `PYTHONPATH=/Users/lanhezheng/vibe-agent pytest tests/backend/agents/test_reviewer_agent.py -v`
Expected: New tests PASS. (Pre-existing `test_reviewer_agent_with_issues` / `test_reviewer_agent_passed` may still fail as before — confirm they fail the SAME way, not a new error.)

- [ ] **Step 5: Commit**

```bash
git add backend/agents/reviewer_agent.py tests/backend/agents/test_reviewer_agent.py
git commit -m "feat: inject static analysis findings into reviewer prompt"
```

---

## Task 4: Config gains default_language

**Files:**
- Modify: `backend/config.py`
- Modify: `tests/backend/test_config.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/backend/test_config.py (append)

def test_default_language_default():
    """default_language defaults to python."""
    from backend.config import Settings
    assert Settings().default_language == "python"


def test_default_language_from_env(monkeypatch):
    monkeypatch.setenv("DEFAULT_LANGUAGE", "typescript")
    from backend.config import Settings
    assert Settings().default_language == "typescript"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=/Users/lanhezheng/vibe-agent pytest tests/backend/test_config.py::test_default_language_default -v`
Expected: FAIL (AttributeError)

- [ ] **Step 3: Write minimal implementation**

In `backend/config.py`, add after the Docker sandbox block:

```python
    # Code generation
    default_language: str = "python"
```

- [ ] **Step 4: Run test**

Run: `PYTHONPATH=/Users/lanhezheng/vibe-agent pytest tests/backend/test_config.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add backend/config.py tests/backend/test_config.py
git commit -m "feat: add default_language setting"
```

---

## Task 5: CoderAgent multi-language directive

**Files:**
- Modify: `backend/agents/coder_agent.py`
- Modify: `tests/backend/agents/test_coder_agent.py`

- [ ] **Step 1: Write the failing test**

Read `tests/backend/agents/test_coder_agent.py` first to match its fixture/mock style, then append:

```python
# tests/backend/agents/test_coder_agent.py (append)

import pytest
from unittest.mock import MagicMock


@pytest.mark.asyncio
async def test_coder_injects_language_directive():
    """Coder includes the target language in the user prompt."""
    from backend.agents.base_agent import AgentContext
    from backend.agents.coder_agent import CoderAgent

    agent = CoderAgent(llm_client=MagicMock())
    captured = {}

    async def fake_call(system_prompt, user_prompt, temperature=0.3):
        captured["user_prompt"] = user_prompt
        return "### FILE: main.ts\n```typescript\nconst x = 1;\n```"

    agent._call_llm = fake_call

    ctx = AgentContext(
        requirement="r", project_id="p", spec="s", architecture="a", language="typescript"
    )
    await agent.run(ctx)

    assert "typescript" in captured["user_prompt"].lower()


@pytest.mark.asyncio
async def test_coder_defaults_to_python_language():
    """When no language is set on context, defaults to python directive."""
    from backend.agents.base_agent import AgentContext
    from backend.agents.coder_agent import CoderAgent

    agent = CoderAgent(llm_client=MagicMock())
    captured = {}

    async def fake_call(system_prompt, user_prompt, temperature=0.3):
        captured["user_prompt"] = user_prompt
        return "### FILE: main.py\n```python\nx = 1\n```"

    agent._call_llm = fake_call

    ctx = AgentContext(requirement="r", project_id="p", spec="s", architecture="a")
    await agent.run(ctx)

    assert "python" in captured["user_prompt"].lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=/Users/lanhezheng/vibe-agent pytest tests/backend/agents/test_coder_agent.py -k language -v`
Expected: FAIL (AgentContext has no `language`; directive missing)

- [ ] **Step 3: Write minimal implementation**

In `backend/agents/base_agent.py`, add a field to `AgentContext` (after `iteration`):

```python
    language: str = "python"  # target code generation language
```

In `backend/agents/coder_agent.py`, add the directive to the user prompt. Change the start of `run()`:

```python
        system_prompt = self._load_prompt("coder")
        language = context.language or "python"
        user_prompt_parts = [
            f"Target language: {language}. Generate all code in {language}.",
            f"Functional Specification:\n{context.spec}",
            f"\nArchitecture:\n{context.architecture}",
        ]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `PYTHONPATH=/Users/lanhezheng/vibe-agent pytest tests/backend/agents/test_coder_agent.py -v`
Expected: New language tests PASS. Confirm the pre-existing `test_coder_agent_generates_code` failure (unrelated, LLM-mock based) is unchanged — not a NEW failure mode.

- [ ] **Step 5: Commit**

```bash
git add backend/agents/base_agent.py backend/agents/coder_agent.py tests/backend/agents/test_coder_agent.py
git commit -m "feat: add target-language directive to CoderAgent"
```

---

## Task 6: SettingsManager (persistence + masking)

**Files:**
- Create: `backend/core/settings_manager.py`
- Create: `tests/backend/core/test_settings_manager.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/backend/core/test_settings_manager.py
"""Tests for SettingsManager."""

import json
import os

from backend.core.settings_manager import SettingsManager

EDITABLE_DEFAULTS = {
    "default_model": "deepseek-v4-pro",
    "max_review_iterations": 5,
    "code_execution_timeout": 30,
    "default_language": "python",
    "use_docker_sandbox": False,
    "anthropic_api_key": "",
    "deepseek_api_key": "",
}


class TestLoad:
    def test_returns_defaults_when_no_file(self, tmp_path):
        path = os.path.join(tmp_path, "settings.json")
        mgr = SettingsManager(path, defaults=EDITABLE_DEFAULTS)
        assert mgr.get_all()["default_model"] == "deepseek-v4-pro"

    def test_overrides_layer_over_defaults(self, tmp_path):
        path = os.path.join(tmp_path, "settings.json")
        with open(path, "w") as f:
            json.dump({"default_model": "glm-4-plus"}, f)
        mgr = SettingsManager(path, defaults=EDITABLE_DEFAULTS)
        assert mgr.get_all()["default_model"] == "glm-4-plus"
        assert mgr.get_all()["max_review_iterations"] == 5


class TestUpdate:
    def test_update_persists(self, tmp_path):
        path = os.path.join(tmp_path, "settings.json")
        mgr = SettingsManager(path, defaults=EDITABLE_DEFAULTS)
        mgr.update({"max_review_iterations": 8})
        # New manager reads the persisted value
        mgr2 = SettingsManager(path, defaults=EDITABLE_DEFAULTS)
        assert mgr2.get_all()["max_review_iterations"] == 8

    def test_update_ignores_unknown_keys(self, tmp_path):
        path = os.path.join(tmp_path, "settings.json")
        mgr = SettingsManager(path, defaults=EDITABLE_DEFAULTS)
        mgr.update({"not_a_real_key": "x"})
        assert "not_a_real_key" not in mgr.get_all()


class TestMasking:
    def test_get_masked_hides_api_keys(self, tmp_path):
        path = os.path.join(tmp_path, "settings.json")
        mgr = SettingsManager(path, defaults=EDITABLE_DEFAULTS)
        mgr.update({"anthropic_api_key": "sk-secret-123"})
        masked = mgr.get_masked()
        assert masked["anthropic_api_key"] == "***"
        # Empty keys show as empty, not masked
        assert masked["deepseek_api_key"] == ""

    def test_get_all_keeps_real_values(self, tmp_path):
        path = os.path.join(tmp_path, "settings.json")
        mgr = SettingsManager(path, defaults=EDITABLE_DEFAULTS)
        mgr.update({"anthropic_api_key": "sk-secret-123"})
        assert mgr.get_all()["anthropic_api_key"] == "sk-secret-123"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=/Users/lanhezheng/vibe-agent pytest tests/backend/core/test_settings_manager.py -v`
Expected: FAIL (ImportError)

- [ ] **Step 3: Write minimal implementation**

```python
# backend/core/settings_manager.py
"""Runtime-editable settings with JSON persistence over defaults."""

import json
import logging
import os

logger = logging.getLogger(__name__)

# Keys whose values must be masked when read for display.
_SECRET_KEYS = {
    "anthropic_api_key",
    "openai_api_key",
    "deepseek_api_key",
    "glm_api_key",
}


class SettingsManager:
    """Holds editable settings: file overrides layered over provided defaults."""

    def __init__(self, path: str, defaults: dict):
        self._path = path
        self._defaults = dict(defaults)
        self._overrides: dict = {}
        self._load()

    def _load(self) -> None:
        if not os.path.isfile(self._path):
            return
        try:
            with open(self._path, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Only accept known keys
            self._overrides = {k: v for k, v in data.items() if k in self._defaults}
        except (json.JSONDecodeError, OSError):
            logger.warning("Could not read settings file %s", self._path)

    def _save(self) -> None:
        os.makedirs(os.path.dirname(self._path) or ".", exist_ok=True)
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(self._overrides, f, indent=2)

    def get_all(self) -> dict:
        """Return effective settings (defaults + overrides), with real secret values."""
        merged = dict(self._defaults)
        merged.update(self._overrides)
        return merged

    def get_masked(self) -> dict:
        """Return effective settings with non-empty secret values masked as '***'."""
        merged = self.get_all()
        for key in _SECRET_KEYS:
            if key in merged and merged[key]:
                merged[key] = "***"
        return merged

    def update(self, changes: dict) -> dict:
        """Apply known changes, persist, and return effective settings.

        Secret values equal to '***' are treated as 'unchanged' and skipped.
        """
        for key, value in changes.items():
            if key not in self._defaults:
                continue
            if key in _SECRET_KEYS and value == "***":
                continue  # masked sentinel — keep existing value
            self._overrides[key] = value
        self._save()
        return self.get_all()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `PYTHONPATH=/Users/lanhezheng/vibe-agent pytest tests/backend/core/test_settings_manager.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add backend/core/settings_manager.py tests/backend/core/test_settings_manager.py
git commit -m "feat: add SettingsManager with JSON persistence and secret masking"
```

---

## Task 7: Settings REST endpoints + LLMClient rebuild + .gitignore

**Files:**
- Modify: `backend/main.py`
- Modify: `.gitignore`

- [ ] **Step 1: Wire SettingsManager into the app**

In `backend/main.py`:

Add import near other core imports:

```python
from backend.core.settings_manager import SettingsManager
```

Add a module-level global next to the other globals (`llm_client`, `state_store`, `ws_manager`):

```python
settings_manager: SettingsManager | None = None
```

In the `lifespan` function, after `settings` is available and before/after `llm_client` is built, initialize the manager with the editable defaults and apply any persisted overrides to the live `LLMClient`:

```python
    global settings_manager
    editable_defaults = {
        "default_model": settings.default_model,
        "fallback_model": settings.fallback_model,
        "max_review_iterations": settings.max_review_iterations,
        "code_execution_timeout": settings.code_execution_timeout,
        "default_language": settings.default_language,
        "use_docker_sandbox": settings.use_docker_sandbox,
        "anthropic_api_key": settings.anthropic_api_key,
        "openai_api_key": settings.openai_api_key,
        "deepseek_api_key": settings.deepseek_api_key,
        "glm_api_key": settings.glm_api_key,
    }
    settings_manager = SettingsManager(
        os.path.join(settings.output_dir, "settings.json"),
        defaults=editable_defaults,
    )
    _apply_settings(settings_manager.get_all())
```

Add the helper + endpoints after the other REST endpoints. `_apply_settings` rebuilds the `LLMClient` and writes through to the live `settings` object so agents (which read `settings`) pick up changes:

```python
def _apply_settings(values: dict) -> None:
    """Push editable settings into the live config and rebuild the LLM client."""
    global llm_client
    settings.default_model = values["default_model"]
    settings.fallback_model = values["fallback_model"]
    settings.max_review_iterations = values["max_review_iterations"]
    settings.code_execution_timeout = values["code_execution_timeout"]
    settings.default_language = values["default_language"]
    settings.use_docker_sandbox = values["use_docker_sandbox"]
    settings.anthropic_api_key = values["anthropic_api_key"]
    settings.openai_api_key = values["openai_api_key"]
    settings.deepseek_api_key = values["deepseek_api_key"]
    settings.glm_api_key = values["glm_api_key"]
    llm_client = LLMClient(
        anthropic_key=settings.anthropic_api_key,
        openai_key=settings.openai_api_key,
        deepseek_key=settings.deepseek_api_key,
        deepseek_base_url=settings.deepseek_base_url,
        glm_key=settings.glm_api_key,
        glm_base_url=settings.glm_base_url,
    )


class UpdateSettingsRequest(BaseModel):
    settings: dict


@app.get("/api/settings")
async def get_settings():
    """Return editable settings with secrets masked."""
    return {"settings": settings_manager.get_masked()}


@app.get("/api/settings/models")
async def get_models():
    """Return available models grouped by provider."""
    return {
        "models": {
            "anthropic": ["claude-3-5-sonnet-20241022"],
            "openai": ["gpt-4o"],
            "deepseek": ["deepseek-v4-pro"],
            "glm": ["glm-4-plus"],
        }
    }


@app.post("/api/settings")
async def update_settings(request: UpdateSettingsRequest):
    """Apply and persist settings changes; rebuild the LLM client."""
    values = settings_manager.update(request.settings)
    _apply_settings(values)
    return {"settings": settings_manager.get_masked()}
```

- [ ] **Step 2: Protect the settings file**

Add to `.gitignore` (create the line if missing):

```
output/settings.json
```

- [ ] **Step 3: Verify routes register and import works**

Run: `PYTHONPATH=/Users/lanhezheng/vibe-agent python -c "from backend.main import app; p=[r.path for r in app.routes]; assert '/api/settings' in p and '/api/settings/models' in p; print('routes OK')"`
Expected: prints `routes OK`

- [ ] **Step 4: Pass the configured language to the workflow's coder context**

In `_run_workflow` in `backend/main.py`, set the language on the context after it is created:

```python
    context = AgentContext(requirement=requirement, project_id=project_id)
    context.language = settings.default_language
```

- [ ] **Step 5: Run backend suite for regressions**

Run: `PYTHONPATH=/Users/lanhezheng/vibe-agent pytest tests/ --ignore=tests/backend/tools/test_docker_sandbox_integration.py -q`
Expected: Only the 5 pre-existing failures; no NEW failures.

- [ ] **Step 6: Commit**

```bash
git add backend/main.py .gitignore
git commit -m "feat: add settings REST endpoints with live LLM client rebuild"
```

---

## Task 8: Frontend settings types + store state

**Files:**
- Modify: `frontend/src/types/index.ts`
- Modify: `frontend/src/store/useStore.ts`

- [ ] **Step 1: Add types**

In `frontend/src/types/index.ts`, append:

```typescript
export interface AppSettings {
  default_model: string;
  fallback_model: string;
  max_review_iterations: number;
  code_execution_timeout: number;
  default_language: string;
  use_docker_sandbox: boolean;
  anthropic_api_key: string;
  openai_api_key: string;
  deepseek_api_key: string;
  glm_api_key: string;
}

export type ModelsByProvider = Record<string, string[]>;
```

- [ ] **Step 2: Add settings-panel open state to the store**

In `frontend/src/store/useStore.ts`:

Add to the `AppState` interface:

```typescript
  isSettingsOpen: boolean;
  setSettingsOpen: (open: boolean) => void;
```

Add to `initialState`:

```typescript
  isSettingsOpen: false,
```

Add the action in the store creator (near `setRunning`):

```typescript
  setSettingsOpen: (isSettingsOpen) => set({ isSettingsOpen }),
```

- [ ] **Step 3: Verify build**

Run: `cd frontend && npm run build`
Expected: Build succeeds.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/types/index.ts frontend/src/store/useStore.ts
git commit -m "feat: add settings types and panel-open state to frontend store"
```

---

## Task 9: SettingsPanel component

**Files:**
- Create: `frontend/src/components/SettingsPanel.tsx`

- [ ] **Step 1: Create the component**

```tsx
// frontend/src/components/SettingsPanel.tsx
import { useEffect, useState } from 'react';
import { useStore } from '../store/useStore';
import type { AppSettings, ModelsByProvider } from '../types';

const PROVIDERS = ['anthropic', 'openai', 'deepseek', 'glm'] as const;

const KEY_FIELD: Record<string, keyof AppSettings> = {
  anthropic: 'anthropic_api_key',
  openai: 'openai_api_key',
  deepseek: 'deepseek_api_key',
  glm: 'glm_api_key',
};

export function SettingsPanel() {
  const isOpen = useStore((s) => s.isSettingsOpen);
  const setOpen = useStore((s) => s.setSettingsOpen);
  const [settings, setSettings] = useState<AppSettings | null>(null);
  const [models, setModels] = useState<ModelsByProvider>({});
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!isOpen) return;
    fetch('/api/settings')
      .then((r) => (r.ok ? r.json() : { settings: null }))
      .then((d) => setSettings(d.settings))
      .catch(() => setSettings(null));
    fetch('/api/settings/models')
      .then((r) => (r.ok ? r.json() : { models: {} }))
      .then((d) => setModels(d.models ?? {}))
      .catch(() => setModels({}));
  }, [isOpen]);

  if (!isOpen) return null;

  const update = (patch: Partial<AppSettings>) =>
    setSettings((prev) => (prev ? { ...prev, ...patch } : prev));

  const save = () => {
    if (!settings) return;
    setSaving(true);
    fetch('/api/settings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ settings }),
    })
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => {
        if (d) setSettings(d.settings);
        setOpen(false);
      })
      .finally(() => setSaving(false));
  };

  const allModels = PROVIDERS.flatMap((p) => models[p] ?? []);

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        right: 0,
        width: 360,
        height: '100vh',
        background: 'var(--bg-secondary)',
        borderLeft: '1px solid var(--border-color)',
        padding: 16,
        overflow: 'auto',
        zIndex: 1000,
        color: 'var(--text-primary)',
        fontSize: 13,
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <strong>Settings</strong>
        <button onClick={() => setOpen(false)} style={{ cursor: 'pointer' }}>✕</button>
      </div>

      {!settings ? (
        <div style={{ color: 'var(--text-muted)' }}>Loading…</div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <label>Default model
            <select
              value={settings.default_model}
              onChange={(e) => update({ default_model: e.target.value })}
              style={{ width: '100%' }}
            >
              {allModels.length === 0 && <option>{settings.default_model}</option>}
              {allModels.map((m) => <option key={m} value={m}>{m}</option>)}
            </select>
          </label>

          {PROVIDERS.map((p) => (
            <label key={p}>{p} API key
              <input
                type="password"
                value={settings[KEY_FIELD[p]] as string}
                placeholder="(unchanged)"
                onChange={(e) => update({ [KEY_FIELD[p]]: e.target.value } as Partial<AppSettings>)}
                style={{ width: '100%' }}
              />
            </label>
          ))}

          <label>Target language
            <select
              value={settings.default_language}
              onChange={(e) => update({ default_language: e.target.value })}
              style={{ width: '100%' }}
            >
              <option value="python">Python</option>
              <option value="typescript">TypeScript</option>
            </select>
          </label>

          <label>Max review iterations
            <input
              type="number"
              min={1}
              max={10}
              value={settings.max_review_iterations}
              onChange={(e) => update({ max_review_iterations: Number(e.target.value) })}
              style={{ width: '100%' }}
            />
          </label>

          <label>Code execution timeout (s)
            <input
              type="number"
              min={1}
              value={settings.code_execution_timeout}
              onChange={(e) => update({ code_execution_timeout: Number(e.target.value) })}
              style={{ width: '100%' }}
            />
          </label>

          <label style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <input
              type="checkbox"
              checked={settings.use_docker_sandbox}
              onChange={(e) => update({ use_docker_sandbox: e.target.checked })}
            />
            Use Docker sandbox
          </label>

          <button onClick={save} disabled={saving} style={{ marginTop: 12, cursor: 'pointer' }}>
            {saving ? 'Saving…' : 'Save'}
          </button>
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Verify build**

Run: `cd frontend && npm run build`
Expected: Build succeeds.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/SettingsPanel.tsx
git commit -m "feat: add SettingsPanel drawer for runtime configuration"
```

---

## Task 10: Mount SettingsPanel + gear button + TS file icons

**Files:**
- Modify: `frontend/src/components/Layout.tsx`
- Modify: `frontend/src/components/FileTree.tsx`
- Modify: `frontend/src/App.tsx`

- [ ] **Step 1: Add a gear button to the sidebar header and mount the panel**

In `frontend/src/components/Layout.tsx`, import the store and panel at the top:

```typescript
import { useStore } from '../store/useStore';
import { SettingsPanel } from './SettingsPanel';
```

In the sidebar header (the `🤖 DevAgent` header div), add a gear button on the right. Replace that header's content with a flex row:

```tsx
        <div style={{ ...headerStyle, justifyContent: 'space-between' }}>
          <span style={{ color: 'var(--accent-blue)' }}>🤖 DevAgent</span>
          <button
            onClick={() => useStore.getState().setSettingsOpen(true)}
            style={{ cursor: 'pointer', background: 'none', border: 'none', fontSize: 16 }}
            title="Settings"
          >
            ⚙️
          </button>
        </div>
```

At the end of the top-level returned fragment (just before the outermost closing `</div>`), mount the panel:

```tsx
      <SettingsPanel />
```

- [ ] **Step 2: Distinguish TypeScript icons in FileTree**

In `frontend/src/components/FileTree.tsx`, replace the `getFileIcon` body's JS/TS line so TS gets a distinct icon:

```typescript
function getFileIcon(filename: string): string {
  if (filename.endsWith('.py')) return '🐍';
  if (filename.endsWith('.ts') || filename.endsWith('.tsx')) return '📘';
  if (filename.endsWith('.js')) return '📙';
  if (filename.endsWith('.json')) return '📋';
  if (filename.endsWith('.md')) return '📝';
  if (filename.endsWith('.html')) return '🌐';
  if (filename.endsWith('.css')) return '🎨';
  return '📄';
}
```

- [ ] **Step 3: (No change needed in App.tsx for wiring, but confirm it builds with the new Layout)**

Run: `cd frontend && npm run build`
Expected: Build succeeds with no TypeScript errors.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/Layout.tsx frontend/src/components/FileTree.tsx
git commit -m "feat: add settings gear button, mount panel, and distinct TS file icons"
```

---

## Self-Review Checklist

**1. Spec coverage:**
- [x] Reviewer + pylint/mypy — Tasks 1, 2, 3
- [x] Multi-language generation (Python + TypeScript) — Tasks 4, 5, plus tsc analysis in Task 1-2 and language wired into workflow in Task 7
- [x] Settings UI (API keys, model, max iters, timeout, language, sandbox) — Tasks 6, 7, 8, 9, 10
- [x] File-tree icons for TS — Task 10
- [x] Static analysis augments (not replaces) the LLM reviewer — Task 3

**2. Placeholder scan:**
- [x] No TBD/TODO; all code complete
- [x] Layout/FileTree edits show exact replacement code; reviewer/coder edits show exact insertion points (implementer reads file first where structure matters)

**3. Type consistency:**
- [x] `Issue` fields (`tool/file/line/column/severity/message/code`) identical across analyzer, tests, reviewer formatting
- [x] `AppSettings` keys match `editable_defaults` / `_apply_settings` keys in `main.py`
- [x] `AgentContext.language` defined (Task 5) before use in CoderAgent and workflow (Task 7)
- [x] Settings endpoints return `{settings: ...}` / `{models: ...}`; frontend reads same shape

**4. DRY / YAGNI:**
- [x] Single `StaticAnalyzer.analyze` dispatcher; per-tool private methods
- [x] `_apply_settings` is the single place that rebuilds LLMClient + writes live settings
- [x] No template engine introduced — directive string only
- [x] Temperature deliberately excluded (user-confirmed)

**5. Test strategy:**
- [x] Backend TDD: StaticAnalyzer, SettingsManager, reviewer injection, coder directive, config
- [x] Backend routes: import-time assertion
- [x] Frontend: `npm run build` typecheck
- [x] Regression guard: 5 pre-existing failures tracked; no new ones

---

## Execution Handoff

Plan complete. Same execution model as Phases 1-2 (inline, TDD, commit per task).
