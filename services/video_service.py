"""FFmpeg conversion and OpenCV keyframe extraction."""

from __future__ import annotations

import logging
import shutil
import subprocess
from pathlib import Path

import cv2

from application.ports import ProgressCallback
from domain.exceptions import VideoProcessingError

LOGGER = logging.getLogger(__name__)


class VideoService:
    """Convert Playwright videos and select visually distinct frames."""

    def __init__(self, sample_interval: float = 0.75, difference_threshold: float = 2.0) -> None:
        self.sample_interval = sample_interval
        self.difference_threshold = difference_threshold

    def convert_to_mp4(self, source: Path, destination: Path) -> Path:
        """Convert the browser WebM recording to broadly compatible MP4."""
        ffmpeg = shutil.which("ffmpeg")
        if not ffmpeg:
            raise VideoProcessingError(
                "FFmpeg est introuvable. Installez-le via l'environnement Conda."
            )
        destination.parent.mkdir(parents=True, exist_ok=True)
        command = [
            ffmpeg,
            "-y",
            "-i",
            str(source),
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(destination),
        ]
        LOGGER.info("Converting %s to %s", source, destination)
        completed = subprocess.run(command, capture_output=True, text=True, check=False)
        if completed.returncode != 0:
            raise VideoProcessingError(
                f"La conversion FFmpeg a échoué: {completed.stderr[-1000:]}"
            )
        return destination

    def extract_keyframes(
        self,
        video_path: Path,
        output_directory: Path,
        progress: ProgressCallback,
    ) -> list[tuple[Path, float]]:
        """Save interval-based frames when their visual content has changed."""
        capture = cv2.VideoCapture(str(video_path))
        if not capture.isOpened():
            raise VideoProcessingError(f"Impossible d'ouvrir la vidéo {video_path}.")

        fps = capture.get(cv2.CAP_PROP_FPS) or 25.0
        frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps if frame_count else 0.0
        stride = max(1, round(fps * self.sample_interval))
        session_directory = output_directory / video_path.parent.name
        session_directory.mkdir(parents=True, exist_ok=True)

        selected: list[tuple[Path, float]] = []
        previous_gray = None
        index = 0
        try:
            while True:
                success, frame = capture.read()
                if not success:
                    break
                if index % stride:
                    index += 1
                    continue

                timestamp = index / fps
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                gray = cv2.resize(gray, (320, 200))
                difference = (
                    float("inf")
                    if previous_gray is None
                    else float(cv2.absdiff(gray, previous_gray).mean())
                )
                if difference >= self.difference_threshold:
                    image_path = session_directory / f"frame_{len(selected):04d}.png"
                    if not cv2.imwrite(str(image_path), frame):
                        raise VideoProcessingError(f"Échec de l'écriture de {image_path}.")
                    selected.append((image_path, timestamp))
                    previous_gray = gray
                progress("Extraction des images clés", timestamp, duration)
                index += 1
        finally:
            capture.release()

        if not selected:
            raise VideoProcessingError("Aucune image clé n'a pu être extraite.")
        LOGGER.info("Extracted %d keyframes from %s", len(selected), video_path)
        return selected
