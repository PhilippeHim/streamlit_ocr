"""Thread-safe background execution for the Streamlit interface."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from threading import Event, Lock, Thread

from application.use_cases import CaptureAndRecognizeUseCase
from domain.models import CaptureSettings, JobStatus, ProcessingResult

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class JobSnapshot:
    """Immutable state consumed by Streamlit reruns."""

    status: JobStatus
    message: str
    elapsed_seconds: float
    total_seconds: float
    result: ProcessingResult | None
    error: str | None


class CaptureJobManager:
    """Run one capture workflow in a worker thread."""

    def __init__(self, use_case: CaptureAndRecognizeUseCase) -> None:
        self._use_case = use_case
        self._lock = Lock()
        self._stop_event = Event()
        self._thread: Thread | None = None
        self._status = JobStatus.IDLE
        self._message = "Prêt"
        self._elapsed_seconds = 0.0
        self._total_seconds = 0.0
        self._result: ProcessingResult | None = None
        self._error: str | None = None

    def start(self, settings: CaptureSettings) -> None:
        """Start a workflow unless another one is already active."""
        with self._lock:
            if self._thread and self._thread.is_alive():
                raise RuntimeError("Une capture est déjà en cours.")
            self._stop_event.clear()
            self._status = JobStatus.RUNNING
            self._message = "Initialisation du navigateur"
            self._elapsed_seconds = 0.0
            self._total_seconds = float(settings.max_duration)
            self._result = None
            self._error = None
            self._thread = Thread(
                target=self._run,
                args=(settings,),
                name="capture-worker",
                daemon=True,
            )
            self._thread.start()

    def stop(self) -> None:
        """Ask the browser loop to stop at its next checkpoint."""
        with self._lock:
            if self._status == JobStatus.RUNNING:
                self._status = JobStatus.STOPPING
                self._message = "Arrêt demandé, finalisation de la vidéo"
                self._stop_event.set()

    def snapshot(self) -> JobSnapshot:
        """Return a consistent view of the current state."""
        with self._lock:
            return JobSnapshot(
                status=self._status,
                message=self._message,
                elapsed_seconds=self._elapsed_seconds,
                total_seconds=self._total_seconds,
                result=self._result,
                error=self._error,
            )

    def _run(self, settings: CaptureSettings) -> None:
        try:
            result = self._use_case.execute(settings, self._stop_event, self._on_progress)
            with self._lock:
                self._result = result
                self._status = (
                    JobStatus.STOPPED if result.capture.stopped_by_user else JobStatus.COMPLETED
                )
                self._message = "Traitement terminé"
        except Exception as exc:  # The UI must surface adapter failures cleanly.
            LOGGER.exception("Capture workflow failed")
            with self._lock:
                self._status = JobStatus.FAILED
                self._message = "Le traitement a échoué"
                self._error = str(exc)

    def _on_progress(self, message: str, elapsed: float, total: float) -> None:
        with self._lock:
            self._message = message
            self._elapsed_seconds = max(0.0, elapsed)
            self._total_seconds = max(0.0, total)

