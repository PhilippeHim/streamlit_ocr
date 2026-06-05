"""Playwright browser capture adapter."""

from __future__ import annotations

import logging
import time
from datetime import datetime
from pathlib import Path
from threading import Event

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import sync_playwright

from application.ports import ProgressCallback
from domain.exceptions import CaptureError
from domain.models import CaptureArtifact, CaptureSettings
from services.video_service import VideoService

LOGGER = logging.getLogger(__name__)


class BrowserService:
    """Navigate, scroll and record a web page with Chromium."""

    def __init__(self, recordings_directory: Path, video_service: VideoService) -> None:
        self.recordings_directory = recordings_directory
        self.video_service = video_service

    def capture(
        self,
        settings: CaptureSettings,
        stop_event: Event,
        progress: ProgressCallback,
    ) -> CaptureArtifact:
        """Record automatic scrolling until the bottom, timeout or user stop."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        session_directory = self.recordings_directory / timestamp
        session_directory.mkdir(parents=True, exist_ok=True)
        source_video = session_directory / "capture.webm"
        mp4_video = session_directory / "capture.mp4"
        started_at = time.monotonic()
        stopped_by_user = False

        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=True)
                context = browser.new_context(
                    viewport={
                        "width": settings.viewport_width,
                        "height": settings.viewport_height,
                    },
                    record_video_dir=str(session_directory),
                    record_video_size={
                        "width": settings.viewport_width,
                        "height": settings.viewport_height,
                    },
                )
                page = context.new_page()
                page.goto(settings.url, wait_until="domcontentloaded", timeout=60_000)
                page.wait_for_timeout(1_000)
                video = page.video

                while True:
                    elapsed = time.monotonic() - started_at
                    progress("Enregistrement et défilement", elapsed, settings.max_duration)
                    if stop_event.is_set():
                        stopped_by_user = True
                        break
                    if elapsed >= settings.max_duration:
                        break

                    metrics = page.evaluate(
                        """(step) => {
                            const root = document.scrollingElement || document.documentElement;
                            const before = root.scrollTop;
                            window.scrollBy({top: step, behavior: "smooth"});
                            return {
                                before,
                                max: Math.max(0, root.scrollHeight - window.innerHeight)
                            };
                        }""",
                        settings.scroll_step,
                    )
                    page.wait_for_timeout(round(settings.scroll_delay * 1000))
                    current = page.evaluate(
                        "() => (document.scrollingElement || document.documentElement).scrollTop"
                    )
                    if current >= metrics["max"] or current == metrics["before"]:
                        break

                page.wait_for_timeout(500)
                context.close()
                if video is None:
                    raise CaptureError("Playwright n'a produit aucune vidéo.")
                video.save_as(str(source_video))
                video.delete()
                browser.close()
        except PlaywrightError as exc:
            raise CaptureError(f"La capture Playwright a échoué: {exc}") from exc

        duration = time.monotonic() - started_at
        self.video_service.convert_to_mp4(source_video, mp4_video)
        return CaptureArtifact(
            source_video=source_video,
            mp4_video=mp4_video,
            duration_seconds=duration,
            stopped_by_user=stopped_by_user,
        )
