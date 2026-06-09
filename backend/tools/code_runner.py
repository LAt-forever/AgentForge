"""Code execution tool for agents."""

import os
import py_compile
import subprocess
import sys
import tempfile


class CodeRunner:
    """Runs and validates Python code safely."""

    def __init__(self, timeout: int = 30):
        self._timeout = timeout

    def validate_syntax(self, code: str) -> tuple[bool, str]:
        """Check Python syntax without executing. Returns (is_valid, error_message)."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            temp_path = f.name

        try:
            py_compile.compile(temp_path, doraise=True)
            return True, ""
        except py_compile.PyCompileError as exc:
            return False, str(exc)
        finally:
            os.unlink(temp_path)

    def run_file(self, file_path: str) -> tuple[str, str, int]:
        """Run a Python file with subprocess. Returns (stdout, stderr, returncode)."""
        result = subprocess.run(
            [sys.executable, file_path],
            capture_output=True,
            text=True,
            timeout=self._timeout,
        )
        return result.stdout, result.stderr, result.returncode

    def run_code(self, code: str) -> tuple[str, str, int]:
        """Write code to temp file, run it, clean up. Returns (stdout, stderr, returncode)."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            temp_path = f.name

        try:
            return self.run_file(temp_path)
        except subprocess.TimeoutExpired:
            return "", f"Execution timed out after {self._timeout} seconds", -1
        finally:
            os.unlink(temp_path)
