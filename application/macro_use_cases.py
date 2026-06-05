"""Application use cases for browser macros."""

from __future__ import annotations

import json
from pathlib import Path
from threading import Event

from application.ports import MacroBrowserPort, OCRPort, ProgressCallback
from domain.macro_models import MacroDefinition, MacroRunResult
from domain.models import OCRDocument
from domain.text_reconstruction import TextReconstructor


class RunMacroUseCase:
    """Execute a validated macro through a browser adapter."""

    def __init__(
        self,
        browser: MacroBrowserPort,
        ocr: OCRPort,
        reconstructor: TextReconstructor,
    ) -> None:
        self.browser = browser
        self.ocr = ocr
        self.reconstructor = reconstructor

    def execute(
        self,
        macro: MacroDefinition,
        stop_event: Event,
        progress: ProgressCallback,
    ) -> MacroRunResult:
        result = self.browser.run_macro(macro, stop_event, progress)
        if not macro.perform_ocr or not result.screenshots:
            return result

        screenshots = [
            (path, float(index))
            for index, path in enumerate(result.screenshots)
        ]
        frames = self.ocr.recognize_frames(screenshots, progress)
        document = OCRDocument(
            title=f"OCR - {macro.name}",
            source_url=macro.start_url,
            text=self.reconstructor.reconstruct(frames),
            frames=frames,
        )
        return MacroRunResult(
            macro_name=result.macro_name,
            screenshots=result.screenshots,
            session_directory=result.session_directory,
            duration_seconds=result.duration_seconds,
            stopped_by_user=result.stopped_by_user,
            document=document,
        )


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
