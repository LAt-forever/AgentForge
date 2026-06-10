"""Runtime-editable settings with JSON persistence over defaults."""

import json
import logging
import os

logger = logging.getLogger(__name__)

# Keys whose values must be masked when read for display.
_SECRET_KEYS = {
    "anthropic_api_key",
    "openai_api_key",
    "deepseek_api_key",
    "glm_api_key",
}


class SettingsManager:
    """Holds editable settings: file overrides layered over provided defaults."""

    def __init__(self, path: str, defaults: dict):
        self._path = path
        self._defaults = dict(defaults)
        self._overrides: dict = {}
        self._load()

    def _load(self) -> None:
        if not os.path.isfile(self._path):
            return
        try:
            with open(self._path, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Only accept known keys
            self._overrides = {k: v for k, v in data.items() if k in self._defaults}
        except (json.JSONDecodeError, OSError):
            logger.warning("Could not read settings file %s", self._path)

    def _save(self) -> None:
        os.makedirs(os.path.dirname(self._path) or ".", exist_ok=True)
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(self._overrides, f, indent=2)

    def get_all(self) -> dict:
        """Return effective settings (defaults + overrides), with real secret values."""
        merged = dict(self._defaults)
        merged.update(self._overrides)
        return merged

    def get_masked(self) -> dict:
        """Return effective settings with non-empty secret values masked as '***'."""
        merged = self.get_all()
        for key in _SECRET_KEYS:
            if key in merged and merged[key]:
                merged[key] = "***"
        return merged

    def update(self, changes: dict) -> dict:
        """Apply known changes, persist, and return effective settings.

        Secret values equal to '***' are treated as 'unchanged' and skipped.
        """
        for key, value in changes.items():
            if key not in self._defaults:
                continue
            if key in _SECRET_KEYS and value == "***":
                continue  # masked sentinel — keep existing value
            self._overrides[key] = value
        self._save()
        return self.get_all()
