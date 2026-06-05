"""Application use cases for browser macros."""

from __future__ import annotations

import json
from pathlib import Path
from threading import Event

from application.ports import MacroBrowserPort, ProgressCallback
from domain.macro_models import MacroDefinition, MacroRunResult


class RunMacroUseCase:
    """Execute a validated macro through a browser adapter."""

    def __init__(self, browser: MacroBrowserPort) -> None:
        self.browser = browser

    def execute(
        self,
        macro: MacroDefinition,
        stop_event: Event,
        progress: ProgressCallback,
    ) -> MacroRunResult:
        return self.browser.run_macro(macro, stop_event, progress)


class MacroRepository:
    """Persist validated macro definitions as readable JSON files."""

    def __init__(self, directory: Path) -> None:
        self.directory = directory
        self.directory.mkdir(parents=True, exist_ok=True)

    def save(self, macro: MacroDefinition) -> Path:
        """Persist a macro and return its configuration path."""
        destination = self.directory / f"{macro.safe_name}.json"
        destination.write_text(
            json.dumps(macro.to_dict(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return destination

    def load(self, path: Path) -> MacroDefinition:
        """Load and validate a persisted macro."""
        raw = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ValueError("La configuration de macro doit être un objet JSON.")
        return MacroDefinition.from_dict(raw)

