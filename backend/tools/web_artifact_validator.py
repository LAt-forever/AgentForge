"""Validation for generated static web artifacts."""

from __future__ import annotations

from html.parser import HTMLParser
from pathlib import PurePosixPath
import os
import shutil
import subprocess
import tempfile
from urllib.parse import unquote, urlparse

from backend.tools.file_manager import FileManager


class _AssetRefParser(HTMLParser):
    """Collect relevant local asset references from index.html."""

    def __init__(self) -> None:
        super().__init__()
        self.refs: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = {
            key.lower(): value
            for key, value in attrs
            if key and value is not None
        }

        if tag.lower() == "script" and "src" in attr_map:
            self.refs.append(("script", attr_map["src"]))
            return

        if tag.lower() != "link" or "href" not in attr_map:
            return

        rel_value = attr_map.get("rel", "")
        rel_tokens = {token.lower() for token in rel_value.split()}
        if "stylesheet" in rel_tokens:
            self.refs.append(("stylesheet", attr_map["href"]))


class WebArtifactValidator:
    """Validate static web artifacts rooted in a FileManager base directory."""

    def __init__(self, file_manager: FileManager):
        self._file_manager = file_manager

    def validate(self) -> dict:
        if not self._file_manager.exists("index.html"):
            return {
                "type": "static_web",
                "status": "missing_entry",
                "preview_url": "",
                "issues": [
                    self._issue(
                        code="missing_entry",
                        message="Missing entry file: index.html",
                        repairable=True,
                    )
                ],
            }

        refs = self._extract_refs(self._file_manager.read_file("index.html"))
        issues = []
        unsafe_issues = []
        missing_issues = []
        syntax_issues = []
        unavailable_issues = []

        for kind, ref in refs:
            if self._is_ignored_ref(ref):
                continue

            normalized_ref = self._normalize_local_ref(ref)
            if self._is_unsafe_local_ref(normalized_ref):
                issue = self._issue(
                    code="unsafe_ref",
                    message=f"Unsafe local reference in index.html: {ref}",
                    repairable=False,
                )
                unsafe_issues.append(issue)
                issues.append(issue)
                continue

            if not self._file_manager.exists(normalized_ref):
                issue = self._issue(
                    code="missing_ref",
                    message=f"Missing local reference in index.html: {ref}",
                    repairable=True,
                )
                missing_issues.append(issue)
                issues.append(issue)
                continue

            if kind == "script" and self._is_javascript_ref(normalized_ref):
                issue = self._validate_javascript_ref(normalized_ref)
                if issue:
                    issues.append(issue)
                    if issue["code"] == "syntax_unavailable":
                        unavailable_issues.append(issue)
                    else:
                        syntax_issues.append(issue)

        if unsafe_issues:
            status = "unsafe_path"
        elif missing_issues:
            status = "invalid_refs"
        elif syntax_issues:
            status = "syntax_error"
        elif unavailable_issues:
            status = "validation_unavailable"
        else:
            status = "ready"
            issues = []

        return {
            "type": "static_web",
            "status": status,
            "preview_url": "",
            "issues": issues,
        }

    def _extract_refs(self, html: str) -> list[tuple[str, str]]:
        parser = _AssetRefParser()
        parser.feed(html)
        return parser.refs

    def _is_ignored_ref(self, ref: str) -> bool:
        stripped_ref = ref.strip()
        if not stripped_ref or stripped_ref.startswith("#"):
            return True

        parsed = urlparse(stripped_ref)
        if parsed.scheme or parsed.netloc:
            return True

        return False

    def _normalize_local_ref(self, ref: str) -> str:
        parsed = urlparse(unquote(ref.strip().replace("\\", "/")))
        return parsed.path

    def _is_unsafe_local_ref(self, ref: str) -> bool:
        if not ref or ref.startswith("/"):
            return True

        path = PurePosixPath(ref)
        return ".." in path.parts

    def _is_javascript_ref(self, ref: str) -> bool:
        return os.path.splitext(ref)[1].lower() == ".js"

    def _validate_javascript_ref(self, ref: str) -> dict | None:
        node_path = shutil.which("node")
        if node_path is None:
            return self._issue(
                code="syntax_unavailable",
                file=ref,
                message=f"Cannot validate JavaScript because node is unavailable: {ref}",
                repairable=False,
            )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as temp:
            temp.write(self._file_manager.read_file(ref))
            temp_path = temp.name

        try:
            result = subprocess.run(
                [node_path, "--check", temp_path],
                capture_output=True,
                text=True,
                timeout=10,
            )
        except subprocess.TimeoutExpired:
            return self._issue(
                code="syntax_error",
                file=ref,
                message=f"JavaScript syntax check timed out: {ref}",
                repairable=True,
            )
        finally:
            os.unlink(temp_path)

        if result.returncode == 0:
            return None

        detail = (result.stderr or result.stdout).strip().splitlines()
        suffix = f": {detail[-1]}" if detail else ""
        return self._issue(
            code="syntax_error",
            file=ref,
            message=f"JavaScript syntax error in {ref}{suffix}",
            repairable=True,
        )

    def _issue(
        self,
        code: str,
        message: str,
        repairable: bool,
        file: str = "index.html",
    ) -> dict:
        return {
            "severity": "error",
            "code": code,
            "file": file,
            "message": message,
            "repairable": repairable,
        }
