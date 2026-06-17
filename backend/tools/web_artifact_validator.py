"""Validation for generated static web artifacts."""

from __future__ import annotations

from html.parser import HTMLParser
from pathlib import PurePosixPath
from urllib.parse import urlparse

from backend.tools.file_manager import FileManager


class _AssetRefParser(HTMLParser):
    """Collect relevant local asset references from index.html."""

    def __init__(self) -> None:
        super().__init__()
        self.refs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = {
            key.lower(): value
            for key, value in attrs
            if key and value is not None
        }

        if tag.lower() == "script" and "src" in attr_map:
            self.refs.append(attr_map["src"])
            return

        if tag.lower() != "link" or "href" not in attr_map:
            return

        rel_value = attr_map.get("rel", "")
        rel_tokens = {token.lower() for token in rel_value.split()}
        if "stylesheet" in rel_tokens:
            self.refs.append(attr_map["href"])


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
        unsafe_issues = []
        missing_issues = []

        for ref in refs:
            if self._is_ignored_ref(ref):
                continue

            normalized_ref = self._normalize_local_ref(ref)
            if self._is_unsafe_local_ref(normalized_ref):
                unsafe_issues.append(
                    self._issue(
                        code="unsafe_ref",
                        message=f"Unsafe local reference in index.html: {ref}",
                        repairable=False,
                    )
                )
                continue

            if not self._file_manager.exists(normalized_ref):
                missing_issues.append(
                    self._issue(
                        code="missing_ref",
                        message=f"Missing local reference in index.html: {ref}",
                        repairable=True,
                    )
                )

        if unsafe_issues:
            status = "unsafe_path"
            issues = unsafe_issues
        elif missing_issues:
            status = "invalid_refs"
            issues = missing_issues
        else:
            status = "ready"
            issues = []

        return {
            "type": "static_web",
            "status": status,
            "preview_url": "",
            "issues": issues,
        }

    def _extract_refs(self, html: str) -> list[str]:
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
        parsed = urlparse(ref.strip().replace("\\", "/"))
        return parsed.path

    def _is_unsafe_local_ref(self, ref: str) -> bool:
        if not ref or ref.startswith("/"):
            return True

        path = PurePosixPath(ref)
        return ".." in path.parts

    def _issue(self, code: str, message: str, repairable: bool) -> dict:
        return {
            "severity": "error",
            "code": code,
            "file": "index.html",
            "message": message,
            "repairable": repairable,
        }
