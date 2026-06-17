"""Tests for WebArtifactValidator."""

from tempfile import TemporaryDirectory

import pytest

from backend.tools.file_manager import FileManager
from backend.tools.web_artifact_validator import WebArtifactValidator


@pytest.fixture
def temp_dir():
    with TemporaryDirectory() as td:
        yield td


@pytest.fixture
def file_manager(temp_dir):
    return FileManager(base_dir=temp_dir)


@pytest.fixture
def validator(file_manager):
    return WebArtifactValidator(file_manager)


class TestWebArtifactValidator:
    def test_three_file_static_app_passes(self, file_manager, validator):
        file_manager.write_file(
            "index.html",
            (
                '<!doctype html><html><head>'
                '<link rel="stylesheet" href="styles.css">'
                '</head><body>'
                '<script src="app.js"></script>'
                "</body></html>"
            ),
        )
        file_manager.write_file("styles.css", "body { color: #222; }")
        file_manager.write_file("app.js", "console.log('ok');")

        result = validator.validate()

        assert result["type"] == "static_web"
        assert result["status"] == "ready"
        assert result["preview_url"] == ""
        assert result["issues"] == []

    def test_single_file_index_html_passes(self, file_manager, validator):
        file_manager.write_file(
            "index.html",
            "<!doctype html><html><body><h1>Hello</h1></body></html>",
        )

        result = validator.validate()

        assert result["status"] == "ready"
        assert result["preview_url"] == ""
        assert result["issues"] == []

    def test_missing_index_html_fails(self, validator):
        result = validator.validate()

        assert result["type"] == "static_web"
        assert result["status"] == "missing_entry"
        assert result["preview_url"] == ""
        assert result["issues"][0]["code"] == "missing_entry"
        assert result["issues"][0]["file"] == "index.html"
        assert result["issues"][0]["repairable"] is True

    def test_missing_referenced_script_fails(self, file_manager, validator):
        file_manager.write_file(
            "index.html",
            '<!doctype html><html><body><script src="app.js"></script></body></html>',
        )

        result = validator.validate()

        assert result["status"] == "invalid_refs"
        assert result["preview_url"] == ""
        assert result["issues"][0]["code"] == "missing_ref"
        assert result["issues"][0]["file"] == "index.html"

    def test_invalid_referenced_javascript_fails(self, file_manager, validator):
        file_manager.write_file(
            "index.html",
            '<!doctype html><html><body><script src="app.js"></script></body></html>',
        )
        file_manager.write_file("app.js", "function broken( {")

        result = validator.validate()

        assert result["status"] == "syntax_error"
        assert result["preview_url"] == ""
        assert result["issues"][0]["code"] == "syntax_error"
        assert result["issues"][0]["file"] == "app.js"
        assert result["issues"][0]["repairable"] is True

    def test_external_references_are_ignored(self, file_manager, validator):
        file_manager.write_file(
            "index.html",
            (
                '<!doctype html><html><head>'
                '<link rel="stylesheet" href="https://cdn.example.com/styles.css">'
                '<link rel="stylesheet" href="data:text/css,body%7Bcolor:red%7D">'
                '</head><body>'
                '<a href="#hero">Jump</a>'
                '<script src="https://cdn.example.com/app.js"></script>'
                '<a href="mailto:test@example.com">Email</a>'
                "</body></html>"
            ),
        )

        result = validator.validate()

        assert result["status"] == "ready"
        assert result["preview_url"] == ""
        assert result["issues"] == []

    def test_path_traversal_reference_fails(self, file_manager, validator):
        file_manager.write_file(
            "index.html",
            '<!doctype html><html><body><script src="..\\\\secret.js"></script></body></html>',
        )

        result = validator.validate()

        assert result["status"] == "unsafe_path"
        assert result["issues"][0]["code"] == "unsafe_ref"

    def test_encoded_path_traversal_reference_fails(self, file_manager, validator):
        file_manager.write_file(
            "index.html",
            '<!doctype html><html><body><script src="%2e%2e%2fsecret.js"></script></body></html>',
        )

        result = validator.validate()

        assert result["status"] == "unsafe_path"
        assert result["issues"][0]["code"] == "unsafe_ref"

    def test_absolute_filesystem_reference_fails(self, file_manager, validator):
        file_manager.write_file(
            "index.html",
            '<!doctype html><html><head><link rel="stylesheet" href="/etc/passwd"></head></html>',
        )

        result = validator.validate()

        assert result["status"] == "unsafe_path"
        assert result["issues"][0]["code"] == "unsafe_ref"

    def test_unsafe_and_missing_refs_are_both_reported(self, file_manager, validator):
        file_manager.write_file(
            "index.html",
            (
                '<!doctype html><html><head>'
                '<link rel="stylesheet" href="styles.css">'
                '</head><body>'
                '<script src="../secret.js"></script>'
                "</body></html>"
            ),
        )

        result = validator.validate()

        assert result["status"] == "unsafe_path"
        assert result["preview_url"] == ""
        assert [issue["code"] for issue in result["issues"]] == [
            "missing_ref",
            "unsafe_ref",
        ]
