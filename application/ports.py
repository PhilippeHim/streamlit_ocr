"""Protocols implemented by infrastructure adapters."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from threading import Event
from typing import Protocol

from domain.macro_models import MacroDefinition, MacroRunResult
from domain.models import CaptureArtifact, CaptureSettings, OCRDocument, OCRFrame

ProgressCallback = Callable[[str, float, float], None]


class BrowserCapturePort(Protocol):
    def capture(
        self,
        settings: CaptureSettings,
        stop_event: Event,
        progress: ProgressCallback,
    ) -> CaptureArtifact:
        """Capture a scrolling web page and return its video files."""


class MacroBrowserPort(Protocol):
    def run_macro(
        self,
        macro: MacroDefinition,
        stop_event: Event,
        progress: ProgressCallback,
    ) -> MacroRunResult:
        """Execute browser actions and return screenshot artifacts."""


class FrameExtractorPort(Protocol):
    def extract_keyframes(
        self,
        video_path: Path,
        output_directory: Path,
        progress: ProgressCallback,
    ) -> list[tuple[Path, float]]:
        """Extract representative frames with their timestamps."""


class OCRPort(Protocol):
    def recognize_frames(
        self,
        frames: list[tuple[Path, float]],
        progress: ProgressCallback,
    ) -> tuple[OCRFrame, ...]:
        """Recognize text in extracted images."""


class ExportPort(Protocol):
    def to_txt(self, document: OCRDocument) -> bytes:
        """Serialize a document as plain text."""

    def to_markdown(self, document: OCRDocument) -> bytes:
        """Serialize a document as Markdown."""

    def to_csv(self, document: OCRDocument) -> bytes:
        """Serialize a document as CSV."""
