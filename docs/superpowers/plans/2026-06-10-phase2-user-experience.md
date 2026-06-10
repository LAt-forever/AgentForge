# Phase 2: User Experience Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Git version tracking per project, a real-time terminal/log panel, a diff viewer, and a project history list so users can observe, review, and revisit agent work.

**Architecture:** A `GitManager` class runs git per project directory and the workflow commits after each agent. Execution and agent logs stream to the frontend via a new `terminal_output` WebSocket message rendered by a `TerminalPanel`. New REST endpoints expose git log/diff for a `DiffViewer`. `StateStore` gains a detailed project listing powering a `ProjectHistory` sidebar list.

**Tech Stack:** Python 3.11, FastAPI, git (subprocess), React 18 + TypeScript, Zustand, Vite

**Verification note:** The frontend has **no test runner**. Verify frontend changes with `cd frontend && npm run build` (runs `tsc` typecheck + Vite build). Backend uses pytest with `PYTHONPATH=/Users/lanhezheng/vibe-agent`.

---

## File Structure

| File | Action | Responsibility |
|------|--------|---------------|
| `backend/tools/git_manager.py` | Create | Per-project git: init, commit, log, diff, status |
| `tests/backend/tools/test_git_manager.py` | Create | Unit tests for GitManager in temp dirs |
| `backend/core/state_store.py` | Modify | Add `list_projects_detailed()` returning metadata |
| `tests/backend/core/test_state_store.py` | Modify | Test `list_projects_detailed()` |
| `backend/main.py` | Modify | Git commits in workflow; new REST endpoints; terminal WS streaming |
| `frontend/src/types/index.ts` | Modify | Add terminal, git, project-summary types; extend WS message union |
| `frontend/src/store/useStore.ts` | Modify | Add terminal lines + project list state |
| `frontend/src/hooks/useWebSocket.ts` | Modify | Handle `terminal_output` messages |
| `frontend/src/components/TerminalPanel.tsx` | Create | Render streamed stdout/stderr/agent logs |
| `frontend/src/components/DiffViewer.tsx` | Create | Render git diff for a commit / working tree |
| `frontend/src/components/ProjectHistory.tsx` | Create | List projects, switch active project |
| `frontend/src/components/Layout.tsx` | Modify | Mount TerminalPanel + ProjectHistory |
| `frontend/src/App.tsx` | Modify | Wire project switching + fetch project list |

---

## Task 1: GitManager core (init, commit, status)

**Files:**
- Create: `backend/tools/git_manager.py`
- Create: `tests/backend/tools/test_git_manager.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/backend/tools/test_git_manager.py
"""Tests for GitManager."""

import os
import subprocess
from tempfile import TemporaryDirectory

import pytest

from backend.tools.git_manager import GitManager, Commit


@pytest.fixture
def temp_output():
    """A temp directory acting as the output base dir."""
    with TemporaryDirectory() as td:
        yield td


@pytest.fixture
def git_manager(temp_output):
    return GitManager(base_dir=temp_output)


def _make_project(base_dir: str, project_id: str) -> str:
    """Create a project directory with one file."""
    proj_dir = os.path.join(base_dir, project_id)
    os.makedirs(proj_dir, exist_ok=True)
    with open(os.path.join(proj_dir, "spec.md"), "w") as f:
        f.write("# Spec\n")
    return proj_dir


class TestInitRepo:
    def test_init_creates_git_dir(self, git_manager, temp_output):
        """init_repo creates a .git directory."""
        _make_project(temp_output, "p1")
        git_manager.init_repo("p1")
        assert os.path.isdir(os.path.join(temp_output, "p1", ".git"))

    def test_init_is_idempotent(self, git_manager, temp_output):
        """Calling init_repo twice does not error."""
        _make_project(temp_output, "p1")
        git_manager.init_repo("p1")
        git_manager.init_repo("p1")
        assert os.path.isdir(os.path.join(temp_output, "p1", ".git"))


class TestCommit:
    def test_commit_creates_commit(self, git_manager, temp_output):
        """commit stages and commits, appearing in log."""
        _make_project(temp_output, "p1")
        git_manager.init_repo("p1")
        git_manager.commit("p1", "spec: add functional specification")
        log = git_manager.get_log("p1")
        assert len(log) == 1
        assert log[0].message == "spec: add functional specification"

    def test_commit_no_changes_is_safe(self, git_manager, temp_output):
        """Committing with no changes does not raise."""
        _make_project(temp_output, "p1")
        git_manager.init_repo("p1")
        git_manager.commit("p1", "first")
        # No file changes since last commit
        git_manager.commit("p1", "second")
        log = git_manager.get_log("p1")
        # Second commit should be skipped (nothing to commit)
        assert len(log) == 1


class TestStatus:
    def test_status_reports_untracked(self, git_manager, temp_output):
        """get_status lists untracked files."""
        _make_project(temp_output, "p1")
        git_manager.init_repo("p1")
        status = git_manager.get_status("p1")
        assert "spec.md" in status["untracked"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=/Users/lanhezheng/vibe-agent pytest tests/backend/tools/test_git_manager.py -v`
Expected: FAIL with ImportError (GitManager, Commit not defined)

- [ ] **Step 3: Write minimal implementation**

```python
# backend/tools/git_manager.py
"""Git operations for project directories."""

import logging
import os
import subprocess
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class Commit:
    """A single git commit."""

    hash: str
    message: str
    timestamp: str


class GitManager:
    """Manages a git repository per project directory."""

    def __init__(self, base_dir: str = "output"):
        self.base_dir = os.path.abspath(base_dir)

    def _project_dir(self, project_id: str) -> str:
        return os.path.join(self.base_dir, project_id)

    def _run(self, project_id: str, args: list[str]) -> subprocess.CompletedProcess:
        """Run a git command in the project directory."""
        return subprocess.run(
            ["git", "-C", self._project_dir(project_id)] + args,
            capture_output=True,
            text=True,
        )

    def init_repo(self, project_id: str) -> None:
        """Initialize a git repo (idempotent) and set a local identity."""
        proj_dir = self._project_dir(project_id)
        os.makedirs(proj_dir, exist_ok=True)
        if os.path.isdir(os.path.join(proj_dir, ".git")):
            return
        self._run(project_id, ["init"])
        # Local identity so commits work without global config
        self._run(project_id, ["config", "user.email", "agent@devagent.local"])
        self._run(project_id, ["config", "user.name", "DevAgent"])

    def commit(self, project_id: str, message: str, files: list[str] | None = None) -> None:
        """Stage files (all by default) and commit. No-op if nothing to commit."""
        if files is None:
            self._run(project_id, ["add", "-A"])
        else:
            self._run(project_id, ["add"] + files)

        # Check if there is anything staged
        status = self._run(project_id, ["status", "--porcelain"])
        if not status.stdout.strip():
            logger.info("No changes to commit for project %s", project_id)
            return

        result = self._run(project_id, ["commit", "-m", message])
        if result.returncode != 0:
            logger.warning(
                "git commit failed for %s: %s", project_id, result.stderr.strip()
            )

    def get_log(self, project_id: str, limit: int = 20) -> list[Commit]:
        """Return commit history, newest first."""
        result = self._run(
            project_id,
            ["log", f"-{limit}", "--pretty=format:%H%x1f%s%x1f%cI"],
        )
        if result.returncode != 0 or not result.stdout.strip():
            return []
        commits = []
        for line in result.stdout.strip().split("\n"):
            parts = line.split("\x1f")
            if len(parts) == 3:
                commits.append(Commit(hash=parts[0], message=parts[1], timestamp=parts[2]))
        return commits

    def get_diff(self, project_id: str, commit_hash: str | None = None) -> str:
        """Return diff. None = working tree vs HEAD; else that commit vs its parent."""
        if commit_hash is None:
            result = self._run(project_id, ["diff", "HEAD"])
        else:
            result = self._run(project_id, ["show", commit_hash])
        return result.stdout

    def get_status(self, project_id: str) -> dict:
        """Return {modified: [...], untracked: [...], staged: [...]}."""
        result = self._run(project_id, ["status", "--porcelain"])
        modified, untracked, staged = [], [], []
        for line in result.stdout.splitlines():
            if not line:
                continue
            code, path = line[:2], line[3:]
            if code == "??":
                untracked.append(path)
            else:
                if code[0] != " " and code[0] != "?":
                    staged.append(path)
                if code[1] != " ":
                    modified.append(path)
        return {"modified": modified, "untracked": untracked, "staged": staged}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `PYTHONPATH=/Users/lanhezheng/vibe-agent pytest tests/backend/tools/test_git_manager.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add backend/tools/git_manager.py tests/backend/tools/test_git_manager.py
git commit -m "feat: add GitManager for per-project version control"
```

---

## Task 2: GitManager log & diff tests

**Files:**
- Modify: `tests/backend/tools/test_git_manager.py`

- [ ] **Step 1: Append failing tests**

```python
# tests/backend/tools/test_git_manager.py (append)

class TestLogAndDiff:
    def test_log_newest_first(self, git_manager, temp_output):
        """get_log returns commits newest-first."""
        proj_dir = _make_project(temp_output, "p1")
        git_manager.init_repo("p1")
        git_manager.commit("p1", "first")
        with open(os.path.join(proj_dir, "main.py"), "w") as f:
            f.write("print('hi')\n")
        git_manager.commit("p1", "second")
        log = git_manager.get_log("p1")
        assert [c.message for c in log] == ["second", "first"]

    def test_log_empty_repo(self, git_manager, temp_output):
        """get_log on a repo with no commits returns empty list."""
        _make_project(temp_output, "p1")
        git_manager.init_repo("p1")
        assert git_manager.get_log("p1") == []

    def test_diff_working_tree(self, git_manager, temp_output):
        """get_diff(None) shows uncommitted changes against HEAD."""
        proj_dir = _make_project(temp_output, "p1")
        git_manager.init_repo("p1")
        git_manager.commit("p1", "first")
        with open(os.path.join(proj_dir, "spec.md"), "w") as f:
            f.write("# Spec\nchanged\n")
        diff = git_manager.get_diff("p1")
        assert "changed" in diff

    def test_diff_specific_commit(self, git_manager, temp_output):
        """get_diff(hash) shows that commit's changes."""
        proj_dir = _make_project(temp_output, "p1")
        git_manager.init_repo("p1")
        git_manager.commit("p1", "first")
        log = git_manager.get_log("p1")
        diff = git_manager.get_diff("p1", log[0].hash)
        assert "spec.md" in diff
```

- [ ] **Step 2: Run tests**

Run: `PYTHONPATH=/Users/lanhezheng/vibe-agent pytest tests/backend/tools/test_git_manager.py -v`
Expected: All PASS (implementation from Task 1 already supports these)

- [ ] **Step 3: Commit**

```bash
git add tests/backend/tools/test_git_manager.py
git commit -m "test: add GitManager log and diff coverage"
```

---

## Task 3: StateStore detailed project listing

**Files:**
- Modify: `backend/core/state_store.py`
- Modify: `tests/backend/core/test_state_store.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/backend/core/test_state_store.py (append a new test class)

class TestListProjectsDetailed:
    """Test detailed project listing for history UI."""

    def test_list_projects_detailed(self, tmp_path):
        from backend.core.state_store import StateStore, WorkflowState

        store = StateStore(base_dir=str(tmp_path))
        store.create_project("p1", "build a calculator")
        store.create_project("p2", "build a todo app")
        store.update_state("p2", WorkflowState.DONE)

        detailed = store.list_projects_detailed()

        assert len(detailed) == 2
        # Each entry has the fields the history UI needs
        by_id = {d["project_id"]: d for d in detailed}
        assert by_id["p1"]["requirement"] == "build a calculator"
        assert by_id["p1"]["state"] == "idle"
        assert by_id["p2"]["state"] == "done"
        assert "updated_at" in by_id["p1"]

    def test_list_projects_detailed_sorted_newest_first(self, tmp_path):
        from backend.core.state_store import StateStore

        store = StateStore(base_dir=str(tmp_path))
        store.create_project("old", "first")
        store.create_project("new", "second")
        # Force a newer updated_at on "new"
        store.update_output("new", "spec", "x")

        detailed = store.list_projects_detailed()
        assert detailed[0]["project_id"] == "new"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=/Users/lanhezheng/vibe-agent pytest tests/backend/core/test_state_store.py::TestListProjectsDetailed -v`
Expected: FAIL (AttributeError: list_projects_detailed)

- [ ] **Step 3: Write minimal implementation**

Add this method to the `StateStore` class in `backend/core/state_store.py`, right after the existing `list_projects` method (around line 146):

```python
    def list_projects_detailed(self) -> list[dict]:
        """List all projects with metadata, newest-updated first."""
        projects = []
        for project in self._cache.values():
            requirement = project.requirement
            projects.append(
                {
                    "project_id": project.id,
                    "state": project.state.value,
                    "requirement": requirement,
                    "requirement_preview": requirement[:50],
                    "iteration_count": project.iteration_count,
                    "created_at": project.created_at,
                    "updated_at": project.updated_at,
                }
            )
        projects.sort(key=lambda p: p["updated_at"], reverse=True)
        return projects
```

- [ ] **Step 4: Run test to verify it passes**

Run: `PYTHONPATH=/Users/lanhezheng/vibe-agent pytest tests/backend/core/test_state_store.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add backend/core/state_store.py tests/backend/core/test_state_store.py
git commit -m "feat: add detailed project listing to StateStore"
```

---

## Task 4: Backend REST endpoints (project list + git log/diff)

**Files:**
- Modify: `backend/main.py`

- [ ] **Step 1: Add endpoints**

In `backend/main.py`, add a `GitManager` import near the other tool imports:

```python
from backend.tools.git_manager import GitManager
```

Add these endpoints after the existing `get_project_file` endpoint (after line 132). Note `GET /api/projects` MUST be registered — there is currently no list endpoint:

```python
@app.get("/api/projects")
async def list_projects():
    """List all projects with metadata for the history view."""
    return {"projects": state_store.list_projects_detailed()}


@app.get("/api/projects/{project_id}/git/log")
async def get_git_log(project_id: str):
    """Return commit history for a project."""
    if state_store.get_project(project_id) is None:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
    gm = GitManager(base_dir=settings.output_dir)
    commits = gm.get_log(project_id)
    return {
        "commits": [
            {"hash": c.hash, "message": c.message, "timestamp": c.timestamp}
            for c in commits
        ]
    }


@app.get("/api/projects/{project_id}/git/diff")
async def get_git_diff_working(project_id: str):
    """Return the working-tree diff against HEAD."""
    if state_store.get_project(project_id) is None:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
    gm = GitManager(base_dir=settings.output_dir)
    return {"diff": gm.get_diff(project_id)}


@app.get("/api/projects/{project_id}/git/diff/{commit_hash}")
async def get_git_diff_commit(project_id: str, commit_hash: str):
    """Return the diff for a specific commit."""
    if state_store.get_project(project_id) is None:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
    gm = GitManager(base_dir=settings.output_dir)
    return {"diff": gm.get_diff(project_id, commit_hash)}
```

- [ ] **Step 2: Verify the app imports and routes register**

Run: `PYTHONPATH=/Users/lanhezheng/vibe-agent python -c "from backend.main import app; paths=[r.path for r in app.routes]; assert '/api/projects' in paths; assert '/api/projects/{project_id}/git/log' in paths; print('routes OK')"`
Expected: prints `routes OK`

- [ ] **Step 3: Commit**

```bash
git add backend/main.py
git commit -m "feat: add project list and git log/diff REST endpoints"
```

---

## Task 5: Workflow git commits + terminal streaming

**Files:**
- Modify: `backend/main.py`

- [ ] **Step 1: Add a terminal-streaming helper**

In `backend/main.py`, add this helper next to `_notify_workflow_state` (near line 264):

```python
async def _send_terminal(project_id: str, stream: str, content: str):
    """Send a terminal output line to the frontend."""
    await ws_manager.send_message(project_id, {
        "type": "terminal_output",
        "project_id": project_id,
        "stream": stream,  # "stdout" | "stderr" | "agent"
        "content": content,
    })
```

- [ ] **Step 2: Initialize git and commit after each agent in `_run_workflow`**

In `_run_workflow` (starts line 154), instantiate the GitManager right after `fm` is created:

```python
    gm = GitManager(base_dir=settings.output_dir)
    gm.init_repo(project_id)
    await _send_terminal(project_id, "agent", f"Initialized project {project_id}\n")
```

After the PM Agent writes `spec.md` (after `state_store.update_output(project_id, "spec", ...)`), add:

```python
        gm.commit(project_id, "spec: add functional specification")
        await _send_terminal(project_id, "agent", "PM Agent completed: spec.md committed\n")
```

After the Architect writes `architecture.md`, add:

```python
        gm.commit(project_id, "arch: add system architecture")
        await _send_terminal(project_id, "agent", "Architect Agent completed: architecture.md committed\n")
```

Inside the review loop, after the coder files are written to disk (after the `for filepath, content in coder_output.files.items(): fm.write_file(...)` block), add:

```python
            gm.commit(project_id, f"coder: iteration {sm._review_count}")
            await _send_terminal(
                project_id, "agent",
                f"Coder Agent wrote {len(coder_output.files)} file(s)\n",
            )
```

After the reviewer writes `review.md` (after `state_store.update_output(project_id, "review", ...)`), add:

```python
            gm.commit(project_id, "review: add review report")
            await _send_terminal(project_id, "agent", "Reviewer Agent completed\n")
```

When syntax errors are found (inside the `if syntax_errors:` block, after building feedback), add:

```python
                for err in syntax_errors:
                    await _send_terminal(project_id, "stderr", err + "\n")
```

- [ ] **Step 3: Verify app still imports**

Run: `PYTHONPATH=/Users/lanhezheng/vibe-agent python -c "import backend.main; print('import OK')"`
Expected: prints `import OK`

- [ ] **Step 4: Run full backend test suite to confirm no regressions**

Run: `PYTHONPATH=/Users/lanhezheng/vibe-agent pytest tests/ --ignore=tests/backend/tools/test_docker_sandbox_integration.py -q`
Expected: The 5 pre-existing agent/llm failures remain; no NEW failures. GitManager + state_store tests PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/main.py
git commit -m "feat: commit per agent step and stream terminal logs in workflow"
```

---

## Task 6: Frontend types + store + WebSocket handling

**Files:**
- Modify: `frontend/src/types/index.ts`
- Modify: `frontend/src/store/useStore.ts`
- Modify: `frontend/src/hooks/useWebSocket.ts`

- [ ] **Step 1: Extend types**

In `frontend/src/types/index.ts`, update the `WebSocketMessage` union and add new types:

```typescript
export interface TerminalLine {
  stream: 'stdout' | 'stderr' | 'agent';
  content: string;
}

export interface ProjectSummary {
  project_id: string;
  state: string;
  requirement: string;
  requirement_preview: string;
  iteration_count: number;
  created_at: string;
  updated_at: string;
}

export interface GitCommit {
  hash: string;
  message: string;
  timestamp: string;
}

export interface WebSocketMessage {
  type: 'agent_status' | 'workflow_state' | 'error' | 'terminal_output';
  project_id: string;
  [key: string]: unknown;
}
```

- [ ] **Step 2: Extend the Zustand store**

In `frontend/src/store/useStore.ts`, add to the `AppState` interface:

```typescript
  terminalLines: TerminalLine[];
  appendTerminalLine: (line: TerminalLine) => void;
  clearTerminal: () => void;
  projectList: ProjectSummary[];
  setProjectList: (projects: ProjectSummary[]) => void;
```

Import the new types at the top:

```typescript
import type { /* existing */ TerminalLine, ProjectSummary } from '../types';
```

In the store creator, add initial state and actions (and include `terminalLines: []` reset in the existing `reset()`):

```typescript
  terminalLines: [],
  appendTerminalLine: (line) =>
    set((state) => ({ terminalLines: [...state.terminalLines, line].slice(-1000) })),
  clearTerminal: () => set({ terminalLines: [] }),
  projectList: [],
  setProjectList: (projects) => set({ projectList: projects }),
```

In the existing `reset()` action, add `terminalLines: []` to the object it sets.

- [ ] **Step 3: Handle terminal messages in the hook**

In `frontend/src/hooks/useWebSocket.ts`, pull the new action from the store (near the other `useStore` selectors):

```typescript
  const appendTerminalLine = useStore((state) => state.appendTerminalLine);
```

Add a branch in `ws.onmessage` after the `error` branch:

```typescript
        } else if (message.type === 'terminal_output') {
          appendTerminalLine({
            stream: message.stream as 'stdout' | 'stderr' | 'agent',
            content: message.content as string,
          });
```

Add `appendTerminalLine` to the `useCallback` dependency array for `connect`.

- [ ] **Step 4: Verify typecheck + build**

Run: `cd frontend && npm run build`
Expected: Build succeeds with no TypeScript errors.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/types/index.ts frontend/src/store/useStore.ts frontend/src/hooks/useWebSocket.ts
git commit -m "feat: add terminal + project-list state and WS handling to frontend"
```

---

## Task 7: TerminalPanel component

**Files:**
- Create: `frontend/src/components/TerminalPanel.tsx`

- [ ] **Step 1: Create the component**

```tsx
// frontend/src/components/TerminalPanel.tsx
import { useEffect, useRef } from 'react';
import { useStore } from '../store/useStore';

const STREAM_COLORS: Record<string, string> = {
  stdout: '#d4d4d4',
  stderr: '#f48771',
  agent: '#6a9955',
};

export function TerminalPanel() {
  const terminalLines = useStore((state) => state.terminalLines);
  const bottomRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [terminalLines]);

  return (
    <div
      style={{
        height: '100%',
        overflow: 'auto',
        background: '#1e1e1e',
        color: '#d4d4d4',
        fontFamily: 'monospace',
        fontSize: 12,
        padding: 8,
        whiteSpace: 'pre-wrap',
      }}
    >
      {terminalLines.length === 0 ? (
        <div style={{ color: '#666' }}>No output yet.</div>
      ) : (
        terminalLines.map((line, i) => (
          <span key={i} style={{ color: STREAM_COLORS[line.stream] ?? '#d4d4d4' }}>
            {line.content}
          </span>
        ))
      )}
      <div ref={bottomRef} />
    </div>
  );
}
```

- [ ] **Step 2: Verify build**

Run: `cd frontend && npm run build`
Expected: Build succeeds.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/TerminalPanel.tsx
git commit -m "feat: add TerminalPanel for streamed agent/execution logs"
```

---

## Task 8: DiffViewer component

**Files:**
- Create: `frontend/src/components/DiffViewer.tsx`

- [ ] **Step 1: Create the component**

```tsx
// frontend/src/components/DiffViewer.tsx
import { useEffect, useState } from 'react';
import type { GitCommit } from '../types';

interface DiffViewerProps {
  projectId: string;
}

function lineColor(line: string): string {
  if (line.startsWith('+') && !line.startsWith('+++')) return '#2ea043';
  if (line.startsWith('-') && !line.startsWith('---')) return '#f85149';
  if (line.startsWith('@@')) return '#58a6ff';
  return '#8b949e';
}

export function DiffViewer({ projectId }: DiffViewerProps) {
  const [commits, setCommits] = useState<GitCommit[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [diff, setDiff] = useState<string>('');

  useEffect(() => {
    if (!projectId) return;
    fetch(`/api/projects/${projectId}/git/log`)
      .then((r) => (r.ok ? r.json() : { commits: [] }))
      .then((d) => setCommits(d.commits ?? []))
      .catch(() => setCommits([]));
  }, [projectId]);

  useEffect(() => {
    if (!projectId || !selected) return;
    fetch(`/api/projects/${projectId}/git/diff/${selected}`)
      .then((r) => (r.ok ? r.json() : { diff: '' }))
      .then((d) => setDiff(d.diff ?? ''))
      .catch(() => setDiff(''));
  }, [projectId, selected]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', fontSize: 12 }}>
      <select
        value={selected ?? ''}
        onChange={(e) => setSelected(e.target.value || null)}
        style={{ margin: 8, background: '#2d2d2d', color: '#ddd', border: '1px solid #444' }}
      >
        <option value="">Select a commit…</option>
        {commits.map((c) => (
          <option key={c.hash} value={c.hash}>
            {c.message}
          </option>
        ))}
      </select>
      <div
        style={{
          flex: 1,
          overflow: 'auto',
          fontFamily: 'monospace',
          background: '#0d1117',
          padding: 8,
          whiteSpace: 'pre-wrap',
        }}
      >
        {diff
          ? diff.split('\n').map((line, i) => (
              <div key={i} style={{ color: lineColor(line) }}>
                {line || ' '}
              </div>
            ))
          : <span style={{ color: '#666' }}>No diff selected.</span>}
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Verify build**

Run: `cd frontend && npm run build`
Expected: Build succeeds.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/DiffViewer.tsx
git commit -m "feat: add DiffViewer for git commit diffs"
```

---

## Task 9: ProjectHistory component

**Files:**
- Create: `frontend/src/components/ProjectHistory.tsx`

- [ ] **Step 1: Create the component**

```tsx
// frontend/src/components/ProjectHistory.tsx
import { useStore } from '../store/useStore';

interface ProjectHistoryProps {
  onSelect: (projectId: string) => void;
}

export function ProjectHistory({ onSelect }: ProjectHistoryProps) {
  const projectList = useStore((state) => state.projectList);
  const activeId = useStore((state) => state.projectId);

  return (
    <div style={{ borderBottom: '1px solid #333', maxHeight: 200, overflow: 'auto' }}>
      <div style={{ padding: '6px 10px', fontSize: 11, color: '#888', textTransform: 'uppercase' }}>
        Projects
      </div>
      {projectList.length === 0 ? (
        <div style={{ padding: '6px 10px', fontSize: 12, color: '#666' }}>No projects yet.</div>
      ) : (
        projectList.map((p) => (
          <div
            key={p.project_id}
            onClick={() => onSelect(p.project_id)}
            style={{
              padding: '6px 10px',
              cursor: 'pointer',
              fontSize: 12,
              background: p.project_id === activeId ? '#2d2d2d' : 'transparent',
              color: '#ddd',
            }}
          >
            <div style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
              {p.requirement_preview || p.project_id}
            </div>
            <div style={{ fontSize: 10, color: '#777' }}>{p.state}</div>
          </div>
        ))
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
git add frontend/src/components/ProjectHistory.tsx
git commit -m "feat: add ProjectHistory sidebar list"
```

---

## Task 10: Wire panels into Layout + App

**Files:**
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/components/Layout.tsx`

- [ ] **Step 1: Add a terminal pane to Layout**

Read `frontend/src/components/Layout.tsx` first to match its existing prop/structure pattern. Add an optional `terminal` prop rendered as a bottom pane under the editor (e.g. a fixed-height region, ~180px, below the editor area). Keep the existing three-pane structure; the terminal sits at the bottom of the center column.

Concretely, change the `LayoutProps` to add `terminal?: React.ReactNode;` and wrap the editor + terminal in a vertical fl/ex column so the editor flexes and the terminal occupies a fixed height with a top border.

- [ ] **Step 2: Wire ProjectHistory, TerminalPanel, and project switching into App**

In `frontend/src/App.tsx`:

Add imports:

```typescript
import { TerminalPanel } from './components/TerminalPanel';
import { ProjectHistory } from './components/ProjectHistory';
```

Pull the new store actions:

```typescript
  const setProjectList = useStore((state) => state.setProjectList);
  const clearTerminal = useStore((state) => state.clearTerminal);
```

Add an effect that fetches the project list on mount and whenever `projectId` changes:

```typescript
  useEffect(() => {
    fetch('/api/projects')
      .then((res) => (res.ok ? res.json() : { projects: [] }))
      .then((data) => setProjectList(data.projects ?? []))
      .catch((err) => console.error('Failed to fetch project list:', err));
  }, [projectId, setProjectList]);
```

Add a handler to switch projects:

```typescript
  const handleSelectProject = useCallback(
    (id: string) => {
      if (id === projectId) return;
      clearTerminal();
      setProjectId(id);
      setTimeout(() => connect(), 0);
      fetch(`/api/projects/${id}`)
        .then((res) => (res.ok ? res.json() : null))
        .then((data) => {
          if (data) {
            setProject({
              project_id: data.project_id,
              state: data.state,
              agent_statuses: data.agent_statuses || {},
              iteration_count: data.iteration_count || 0,
              outputs: data.outputs || {},
            });
            setRunning(data.state !== 'done');
          }
        })
        .catch((err) => console.error('Failed to load project:', err));
    },
    [projectId, clearTerminal, setProjectId, connect, setProject, setRunning]
  );
```

Update the `sidebar` JSX to render `ProjectHistory` above `FileTree`:

```tsx
  const sidebar = (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <ProjectHistory onSelect={handleSelectProject} />
      <div style={{ flex: 1, overflow: 'auto' }}>
        <FileTree />
      </div>
      <ChatInput onSubmit={handleSubmit} />
    </div>
  );
```

Pass the terminal pane to `Layout`:

```tsx
    <Layout
      sidebar={sidebar}
      editor={<CodeEditor />}
      agentPanel={<AgentPanel />}
      terminal={<TerminalPanel />}
    />
```

- [ ] **Step 3: Verify build**

Run: `cd frontend && npm run build`
Expected: Build succeeds with no TypeScript errors.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/App.tsx frontend/src/components/Layout.tsx
git commit -m "feat: wire ProjectHistory and TerminalPanel into app layout"
```

---

## Self-Review Checklist

**1. Spec coverage:**
- [x] Git integration (init + commit per agent) — Tasks 1, 5
- [x] Git log/diff API + GitManager — Tasks 1, 2, 4
- [x] Terminal/log panel (WS stream + component) — Tasks 5, 6, 7
- [x] Diff viewer — Tasks 4, 8
- [x] Project history list — Tasks 3, 4, 9, 10

**2. Placeholder scan:**
- [x] No TBD/TODO; all code complete
- [x] Layout edit (Task 10 Step 1) describes exact prop + structure change rather than pasting unseen file — implementer must Read Layout.tsx first (noted explicitly)

**3. Type consistency:**
- [x] `Commit` dataclass: `hash/message/timestamp` used identically in GitManager, REST, frontend `GitCommit`
- [x] `terminal_output` message shape (`stream`, `content`) matches between `_send_terminal`, WS hook, `TerminalLine`
- [x] `list_projects_detailed()` dict keys match `ProjectSummary` fields
- [x] New WS message type added to the `WebSocketMessage` union

**4. DRY / YAGNI:**
- [x] Single `GitManager._run` helper for all git calls
- [x] Reuse existing `ws_manager.send_message` pattern
- [x] No diff2html dependency — lightweight inline diff rendering (avoids new npm dep)

**5. Test strategy:**
- [x] Backend: pytest TDD (GitManager, StateStore)
- [x] Backend routes: import-time assertion (Task 4)
- [x] Frontend: `npm run build` (tsc typecheck) — no test runner exists, documented in header

---

## Execution Handoff

Plan complete. Same execution model as Phase 1 (Subagent-Driven, but executed inline in this session with TDD + commit per task).
