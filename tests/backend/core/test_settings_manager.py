"""Tests for SettingsManager."""

import json
import os

from backend.core.settings_manager import SettingsManager

EDITABLE_DEFAULTS = {
    "default_model": "deepseek-v4-pro",
    "max_review_iterations": 5,
    "code_execution_timeout": 30,
    "default_language": "python",
    "use_docker_sandbox": False,
    "anthropic_api_key": "",
    "deepseek_api_key": "",
}


class TestLoad:
    def test_returns_defaults_when_no_file(self, tmp_path):
        path = os.path.join(tmp_path, "settings.json")
        mgr = SettingsManager(path, defaults=EDITABLE_DEFAULTS)
        assert mgr.get_all()["default_model"] == "deepseek-v4-pro"

    def test_overrides_layer_over_defaults(self, tmp_path):
        path = os.path.join(tmp_path, "settings.json")
        with open(path, "w") as f:
            json.dump({"default_model": "glm-4-plus"}, f)
        mgr = SettingsManager(path, defaults=EDITABLE_DEFAULTS)
        assert mgr.get_all()["default_model"] == "glm-4-plus"
        assert mgr.get_all()["max_review_iterations"] == 5


class TestUpdate:
    def test_update_persists(self, tmp_path):
        path = os.path.join(tmp_path, "settings.json")
        mgr = SettingsManager(path, defaults=EDITABLE_DEFAULTS)
        mgr.update({"max_review_iterations": 8})
        mgr2 = SettingsManager(path, defaults=EDITABLE_DEFAULTS)
        assert mgr2.get_all()["max_review_iterations"] == 8

    def test_update_ignores_unknown_keys(self, tmp_path):
        path = os.path.join(tmp_path, "settings.json")
        mgr = SettingsManager(path, defaults=EDITABLE_DEFAULTS)
        mgr.update({"not_a_real_key": "x"})
        assert "not_a_real_key" not in mgr.get_all()


class TestMasking:
    def test_get_masked_hides_api_keys(self, tmp_path):
        path = os.path.join(tmp_path, "settings.json")
        mgr = SettingsManager(path, defaults=EDITABLE_DEFAULTS)
        mgr.update({"anthropic_api_key": "sk-secret-123"})
        masked = mgr.get_masked()
        assert masked["anthropic_api_key"] == "***"
        assert masked["deepseek_api_key"] == ""

    def test_get_all_keeps_real_values(self, tmp_path):
        path = os.path.join(tmp_path, "settings.json")
        mgr = SettingsManager(path, defaults=EDITABLE_DEFAULTS)
        mgr.update({"anthropic_api_key": "sk-secret-123"})
        assert mgr.get_all()["anthropic_api_key"] == "sk-secret-123"

    def test_update_skips_masked_sentinel(self, tmp_path):
        """Updating with '***' keeps the existing secret rather than overwriting."""
        path = os.path.join(tmp_path, "settings.json")
        mgr = SettingsManager(path, defaults=EDITABLE_DEFAULTS)
        mgr.update({"anthropic_api_key": "sk-real"})
        mgr.update({"anthropic_api_key": "***", "default_model": "glm-4-plus"})
        assert mgr.get_all()["anthropic_api_key"] == "sk-real"
        assert mgr.get_all()["default_model"] == "glm-4-plus"
