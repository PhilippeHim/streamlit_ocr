"""Thread-safe background manager for browser macro execution."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from threading import Event, Lock, Thread

from application.macro_use_cases import RunMacroUseCase
from domain.macro_models import MacroDefinition, MacroRunResult
from domain.models import JobStatus

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class MacroJobSnapshot:
    """Immutable macro execution state for Streamlit."""

    status: JobStatus
    message: str
    current_step: float
    total_steps: float
    result: MacroRunResult | None
    error: str | None


class MacroJobManager:
    """Execute one browser macro at a time in a worker thread."""

    def __init__(self, use_case: RunMacroUseCase) -> None:
        self._use_case = use_case
        self._lock = Lock()
        self._stop_event = Event()
        self._thread: Thread | None = None
        self._status = JobStatus.IDLE
        self._message = "Prêt"
        self._current_step = 0.0
        self._total_steps = 1.0
        self._result: MacroRunResult | None = None
        self._error: str | None = None

    def start(self, macro: MacroDefinition) -> None:
        """Start a macro unless one is already running."""
        with self._lock:
            if self._thread and self._thread.is_alive():
                raise RuntimeError("Une macro est déjà en cours.")
            self._stop_event.clear()
            self._status = JobStatus.RUNNING
            self._message = "Initialisation du navigateur"
            self._current_step = 0.0
            self._total_steps = float(max(1, len(macro.actions) + 1))
            self._result = None
            self._error = None
            self._thread = Thread(
                target=self._run,
                args=(macro,),
                name="macro-worker",
                daemon=True,
            )
            self._thread.start()

    def stop(self) -> None:
        """Request a graceful stop between two browser actions."""
        with self._lock:
            if self._status == JobStatus.RUNNING:
                self._status = JobStatus.STOPPING
                self._message = "Arrêt demandé"
                self._stop_event.set()

    def snapshot(self) -> MacroJobSnapshot:
        """Return a consistent snapshot."""
        with self._lock:
            return MacroJobSnapshot(
                status=self._status,
                message=self._message,
                current_step=self._current_step,
                total_steps=self._total_steps,
                result=self._result,
                error=self._error,
            )

    def _run(self, macro: MacroDefinition) -> None:
        try:
            result = self._use_case.execute(macro, self._stop_event, self._on_progress)
            with self._lock:
                self._result = result
                self._status = (
                    JobStatus.STOPPED if result.stopped_by_user else JobStatus.COMPLETED
                )
                self._message = "Macro terminée"
        except Exception as exc:
            LOGGER.exception("Browser macro failed")
            with self._lock:
                self._status = JobStatus.FAILED
                self._message = "La macro a échoué"
                self._error = str(exc)

    def _on_progress(self, message: str, current: float, total: float) -> None:
        with self._lock:
            self._message = message
            self._current_step = max(0.0, current)
            self._total_steps = max(1.0, total)

