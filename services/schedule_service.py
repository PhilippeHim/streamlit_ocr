"""Generate operating-system scheduler configuration for saved macros."""

from __future__ import annotations

import plistlib
import re
from pathlib import Path


class ScheduleService:
    """Create a macOS launchd agent for a daily macro execution."""

    def __init__(self, project_root: Path, python_executable: Path) -> None:
        self.project_root = project_root
        self.python_executable = python_executable

    def create_macos_daily_schedule(
        self,
        macro_path: Path,
        macro_name: str,
        hour: int = 4,
        minute: int = 0,
    ) -> Path:
        """Write a launchd plist in the project data directory."""
        if not 0 <= hour <= 23 or not 0 <= minute <= 59:
            raise ValueError("L'heure planifiée est invalide.")

        safe_name = re.sub(r"[^a-zA-Z0-9.-]+", "-", macro_name).strip(".-") or "macro"
        label = f"com.streamlit-ocr.{safe_name.lower()}"
        schedules_directory = self.project_root / "data" / "schedules"
        logs_directory = self.project_root / "data" / "scheduled_logs"
        schedules_directory.mkdir(parents=True, exist_ok=True)
        logs_directory.mkdir(parents=True, exist_ok=True)
        destination = schedules_directory / f"{label}.plist"

        payload = {
            "Label": label,
            "ProgramArguments": [
                str(self.python_executable),
                str(self.project_root / "run_macro.py"),
                "--config",
                str(macro_path.resolve()),
                "--headless",
            ],
            "WorkingDirectory": str(self.project_root),
            "StartCalendarInterval": {"Hour": hour, "Minute": minute},
            "StandardOutPath": str(logs_directory / f"{safe_name}.out.log"),
            "StandardErrorPath": str(logs_directory / f"{safe_name}.error.log"),
            "ProcessType": "Background",
        }
        with destination.open("wb") as stream:
            plistlib.dump(payload, stream, sort_keys=False)
        return destination

