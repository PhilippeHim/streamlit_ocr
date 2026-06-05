"""Application use cases."""

from __future__ import annotations

import logging
from pathlib import Path
from threading import Event

from application.ports import BrowserCapturePort, FrameExtractorPort, OCRPort, ProgressCallback
from domain.models import CaptureSettings, OCRDocument, ProcessingResult
from domain.text_reconstruction import TextReconstructor

LOGGER = logging.getLogger(__name__)


class CaptureAndRecognizeUseCase:
    """Coordinate browser recording, frame extraction and OCR."""

    def __init__(
        self,
        browser: BrowserCapturePort,
        frame_extractor: FrameExtractorPort,
        ocr: OCRPort,
        reconstructor: TextReconstructor,
        screenshots_directory: Path,
    ) -> None:
        self.browser = browser
        self.frame_extractor = frame_extractor
        self.ocr = ocr
        self.reconstructor = reconstructor
        self.screenshots_directory = screenshots_directory

    def execute(
        self,
        settings: CaptureSettings,
        stop_event: Event,
        progress: ProgressCallback,
    ) -> ProcessingResult:
        """Run the complete workflow and return persisted artifacts."""
        LOGGER.info("Starting capture workflow for %s", settings.url)
        capture = self.browser.capture(settings, stop_event, progress)

        progress("Extraction des images clés", 0.0, capture.duration_seconds)
        frame_files = self.frame_extractor.extract_keyframes(
            capture.mp4_video,
            self.screenshots_directory,
            progress,
        )
        frames = self.ocr.recognize_frames(frame_files, progress)
        text = self.reconstructor.reconstruct(frames)
        document = OCRDocument(
            title="Capture OCR",
            source_url=settings.url,
            text=text,
            frames=frames,
        )
        progress("Traitement terminé", capture.duration_seconds, capture.duration_seconds)
        LOGGER.info("Capture workflow completed with %d OCR frames", len(frames))
        return ProcessingResult(capture=capture, document=document)

