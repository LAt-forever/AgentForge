"""Tests for the FileManager tool."""

import os
import pytest
from tempfile import TemporaryDirectory

from backend.tools.file_manager import FileManager


@pytest.fixture
def temp_dir():
    with TemporaryDirectory() as td:
        yield td


@pytest.fixture
def file_manager(temp_dir):
    return FileManager(base_dir=temp_dir)


class TestWriteAndReadFile:
    """Test writing and reading files."""

    def test_write_and_read_file(self, file_manager, temp_dir):
        """Write a file and read it back."""
        rel_path = "test_file.txt"
        content = "Hello, World!"

        abs_path = file_manager.write_file(rel_path, content)

        assert os.path.exists(abs_path)
        assert abs_path == os.path.join(temp_dir, rel_path)

        read_content = file_manager.read_file(rel_path)
        assert read_content == content

    def test_write_nested_file(self, file_manager, temp_dir):
        """Write a file in a nested directory."""
        rel_path = "sub/dir/nested.txt"
        content = "Nested content"

        abs_path = file_manager.write_file(rel_path, content)

        assert os.path.exists(abs_path)
        assert abs_path == os.path.join(temp_dir, rel_path)

        read_content = file_manager.read_file(rel_path)
        assert read_content == content


class TestListFiles:
    """Test listing files recursively."""

    def test_list_files(self, file_manager):
        """List files recursively, sorted."""
        file_manager.write_file("a.txt", "A")
        file_manager.write_file("b/c.txt", "C")
        file_manager.write_file("b/d.txt", "D")
        file_manager.write_file("e/f/g.txt", "G")

        files = file_manager.list_files()

        assert files == ["a.txt", "b/c.txt", "b/d.txt", "e/f/g.txt"]

    def test_list_files_empty(self, file_manager):
        """List files in empty directory."""
        files = file_manager.list_files()
        assert files == []

    def test_list_files_excludes_git_internals(self, file_manager, temp_dir):
        """Files under a .git directory are not listed."""
        import os

        file_manager.write_file("main.py", "print('hi')")
        # Simulate a git repo's internal files
        os.makedirs(os.path.join(temp_dir, ".git", "objects"), exist_ok=True)
        with open(os.path.join(temp_dir, ".git", "HEAD"), "w") as f:
            f.write("ref: refs/heads/main\n")
        with open(os.path.join(temp_dir, ".git", "objects", "abc"), "w") as f:
            f.write("blob")

        files = file_manager.list_files()
        assert files == ["main.py"]
        assert not any(f.startswith(".git/") for f in files)

    def test_list_files_excludes_hidden_dirs(self, file_manager, temp_dir):
        """Files under any dotted directory are not listed."""
        import os

        file_manager.write_file("app.py", "x = 1")
        os.makedirs(os.path.join(temp_dir, ".cache"), exist_ok=True)
        with open(os.path.join(temp_dir, ".cache", "junk"), "w") as f:
            f.write("noise")

        files = file_manager.list_files()
        assert files == ["app.py"]


class TestFileExists:
    """Test file existence check."""

    def test_file_exists(self, file_manager):
        """Check if a file exists."""
        file_manager.write_file("exists.txt", "yes")

        assert file_manager.exists("exists.txt") is True
        assert file_manager.exists("missing.txt") is False

    def test_exists_nested(self, file_manager):
        """Check nested file existence."""
        file_manager.write_file("sub/dir/file.txt", "content")

        assert file_manager.exists("sub/dir/file.txt") is True
        assert file_manager.exists("sub/dir/missing.txt") is False


class TestDeleteFile:
    """Test deleting files."""

    def test_delete_file(self, file_manager):
        """Delete a file."""
        file_manager.write_file("to_delete.txt", "bye")
        assert file_manager.exists("to_delete.txt") is True

        file_manager.delete_file("to_delete.txt")
        assert file_manager.exists("to_delete.txt") is False


class TestGetAbsolutePath:
    """Test getting absolute path."""

    def test_get_absolute_path(self, file_manager, temp_dir):
        """Get absolute path for a relative path."""
        abs_path = file_manager.get_absolute_path("some/file.txt")
        assert abs_path == os.path.join(temp_dir, "some/file.txt")


class TestInit:
    """Test FileManager initialization."""

    def test_creates_directory_if_not_exists(self, temp_dir):
        """Create base directory if it doesn't exist."""
        new_dir = os.path.join(temp_dir, "new_base")
        assert not os.path.exists(new_dir)

        fm = FileManager(base_dir=new_dir)
        assert os.path.isdir(new_dir)
