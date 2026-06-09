"""File management tool for agents."""

import os


class FileManager:
    """Manages files within a base directory."""

    def __init__(self, base_dir: str):
        self._base_dir = os.path.abspath(base_dir)
        os.makedirs(self._base_dir, exist_ok=True)

    def _resolve_path(self, relative_path: str) -> str:
        """Resolve a relative path to an absolute path within base_dir."""
        abs_path = os.path.abspath(os.path.join(self._base_dir, relative_path))
        # Security: ensure the resolved path is within base_dir
        if not abs_path.startswith(self._base_dir + os.sep) and abs_path != self._base_dir:
            raise ValueError(f"Path '{relative_path}' escapes base directory")
        return abs_path

    def write_file(self, relative_path: str, content: str) -> str:
        """Write file content, create parent dirs, return absolute path."""
        abs_path = self._resolve_path(relative_path)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, "w", encoding="utf-8") as f:
            f.write(content)
        return abs_path

    def read_file(self, relative_path: str) -> str:
        """Read file content."""
        abs_path = self._resolve_path(relative_path)
        with open(abs_path, "r", encoding="utf-8") as f:
            return f.read()

    def exists(self, relative_path: str) -> bool:
        """Check if a file exists."""
        abs_path = self._resolve_path(relative_path)
        return os.path.exists(abs_path)

    def list_files(self) -> list[str]:
        """Recursively list all files as relative paths, sorted."""
        files = []
        for root, _dirs, filenames in os.walk(self._base_dir):
            for filename in filenames:
                abs_path = os.path.join(root, filename)
                rel_path = os.path.relpath(abs_path, self._base_dir)
                files.append(rel_path)
        return sorted(files)

    def delete_file(self, relative_path: str) -> None:
        """Delete a file."""
        abs_path = self._resolve_path(relative_path)
        os.remove(abs_path)

    def get_absolute_path(self, relative_path: str) -> str:
        """Get absolute path for a relative path."""
        return self._resolve_path(relative_path)
