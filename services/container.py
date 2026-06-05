"""Composition root for concrete application dependencies."""

from __future__ import annotations

from pathlib import Path

from application.job_manager import CaptureJobManager
from application.use_cases import CaptureAndRecognizeUseCase
from domain.text_reconstruction import TextReconstructor
from services.browser_service import BrowserService
from services.ocr_service import OCRService
from services.video_service import VideoService


def build_job_manager(project_root: Path) -> CaptureJobManager:
    """Build the dependency graph without coupling it to Streamlit."""
    recordings = project_root / "recordings"
    screenshots = project_root / "screenshots"
    recordings.mkdir(parents=True, exist_ok=True)
    screenshots.mkdir(parents=True, exist_ok=True)

    video_service = VideoService()
    browser_service = BrowserService(recordings, video_service)
    use_case = CaptureAndRecognizeUseCase(
        browser=browser_service,
        frame_extractor=video_service,
        ocr=OCRService(),
        reconstructor=TextReconstructor(),
        screenshots_directory=screenshots,
    )
    return CaptureJobManager(use_case)

