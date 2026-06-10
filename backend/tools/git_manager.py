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

    def commit(
        self, project_id: str, message: str, files: list[str] | None = None
    ) -> None:
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
                commits.append(
                    Commit(hash=parts[0], message=parts[1], timestamp=parts[2])
                )
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
