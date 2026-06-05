"""Local persistence for non-sensitive user preferences."""

from __future__ import annotations

import json
import logging
from pathlib import Path

LOGGER = logging.getLogger(__name__)


class PreferencesService:
    """Store lightweight application preferences as JSON."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def load_last_url(self, default: str = "https://example.com") -> str:
        """Return the last saved URL or a safe default."""
        if not self.path.exists():
            return default
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            value = data.get("last_url") if isinstance(data, dict) else None
            return value.strip() if isinstance(value, str) and value.strip() else default
        except (OSError, json.JSONDecodeError):
            LOGGER.warning("Unable to read preferences from %s", self.path)
            return default

    def save_last_url(self, url: str) -> None:
        """Persist the last validated capture URL."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = self.path.with_suffix(".tmp")
        temporary_path.write_text(
            json.dumps({"last_url": url}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        temporary_path.replace(self.path)

