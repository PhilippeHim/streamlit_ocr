"""Core entities and value objects."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from urllib.parse import urlparse

from domain.exceptions import InvalidURLError


class JobStatus(StrEnum):
    """Lifecycle of a capture job."""

    IDLE = "idle"
    RUNNING = "running"
    STOPPING = "stopping"
    COMPLETED = "completed"
    STOPPED = "stopped"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class CaptureSettings:
    """Parameters controlling navigation and automatic scrolling."""

    url: str
    scroll_step: int = 700
    scroll_delay: float = 0.8
    max_duration: int = 120
    viewport_width: int = 1440
    viewport_height: int = 900

    def __post_init__(self) -> None:
        normalized_url = self.url.strip()
        parsed = urlparse(normalized_url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise InvalidURLError("L'URL doit être une adresse HTTP ou HTTPS complète.")
        object.__setattr__(self, "url", normalized_url)
        if self.scroll_step < 100:
            raise ValueError("Le pas de défilement doit être supérieur ou égal à 100 px.")
        if self.scroll_delay < 0.1:
            raise ValueError("Le délai de défilement doit être supérieur ou égal à 0,1 s.")
        if self.max_duration < 1:
            raise ValueError("La durée maximale doit être positive.")


@dataclass(frozen=True, slots=True)
class CaptureArtifact:
    """Files and timing produced by browser capture."""

    source_video: Path
    mp4_video: Path
    duration_seconds: float
    stopped_by_user: bool = False


@dataclass(frozen=True, slots=True)
class OCRLine:
    """A recognized line and its relative vertical position."""

    text: str
    y_ratio: float
    confidence: float


@dataclass(frozen=True, slots=True)
class OCRFrame:
    """OCR output associated with one extracted video frame."""

    image_path: Path
    timestamp_seconds: float
    lines: tuple[OCRLine, ...]


@dataclass(frozen=True, slots=True)
class OCRDocument:
    """Final reconstructed document."""

    title: str
    source_url: str
    text: str
    frames: tuple[OCRFrame, ...]
    created_at: datetime = field(default_factory=datetime.now)


@dataclass(frozen=True, slots=True)
class ProcessingResult:
    """All artifacts returned to the presentation layer."""

    capture: CaptureArtifact
    document: OCRDocument
