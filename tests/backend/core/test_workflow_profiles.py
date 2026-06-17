"""Tests for workflow profile resolution."""

from backend.core.workflow_profiles import (
    DEFAULT_PROFILE,
    STATIC_WEB_PROFILE,
    get_workflow_profile,
    resolve_workflow_profile,
)


class TestGetWorkflowProfile:
    """Test fetching workflow profile definitions."""

    def test_default_profile_definition(self):
        """Default profile exposes standard labels and no preview."""
        profile = get_workflow_profile(DEFAULT_PROFILE)

        assert profile.name == DEFAULT_PROFILE
        assert profile.display_name == "Default"
        assert profile.stage_labels == ("PM", "Architect", "Coder", "Reviewer")
        assert profile.prompt_context == ""
        assert profile.validators == ()
        assert profile.preview_enabled is False

    def test_static_web_profile_definition(self):
        """Static web profile exposes browser-oriented workflow metadata."""
        profile = get_workflow_profile(STATIC_WEB_PROFILE)

        assert profile.name == STATIC_WEB_PROFILE
        assert profile.display_name == "Web App"
        assert profile.stage_labels == (
            "Product Brief",
            "Web Structure",
            "Frontend Build",
            "Web Review",
        )
        assert "browser-ready static files" in profile.prompt_context
        assert "index.html" in profile.prompt_context
        assert "style.css" in profile.prompt_context
        assert "script.js" in profile.prompt_context
        assert "avoid external/CDN runtime deps" in profile.prompt_context
        assert "interactive web page" in profile.prompt_context
        assert profile.validators == ("web_artifact",)
        assert profile.preview_enabled is True

    def test_unknown_profile_falls_back_to_default(self):
        """Unknown profile names return the default profile."""
        profile = get_workflow_profile("missing")

        assert profile.name == DEFAULT_PROFILE


class TestResolveWorkflowProfile:
    """Test workflow profile selection."""

    def test_resolves_static_web_for_english_requirement(self):
        """English static-web terms select the web app workflow."""
        profile = resolve_workflow_profile(
            "Build a browser-based landing page with HTML, CSS, and JavaScript."
        )

        assert profile.name == STATIC_WEB_PROFILE

    def test_resolves_static_web_for_chinese_requirement(self):
        """Chinese static-web terms select the web app workflow."""
        profile = resolve_workflow_profile("请帮我做一个静态网页，用 HTML/CSS/JS 实现。")

        assert profile.name == STATIC_WEB_PROFILE

    def test_resolves_default_for_cli_requirement(self):
        """Non-web requirements stay on the default workflow."""
        profile = resolve_workflow_profile("Build a CLI tool that parses CSV files.")

        assert profile.name == DEFAULT_PROFILE

    def test_explicit_override_wins(self):
        """Explicit workflow selection overrides heuristics."""
        profile = resolve_workflow_profile(
            "Build a CLI tool that parses CSV files.",
            explicit=STATIC_WEB_PROFILE,
        )

        assert profile.name == STATIC_WEB_PROFILE
