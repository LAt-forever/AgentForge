"""Tests for GitManager."""

import os
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
