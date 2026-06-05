"""Domain models for browser macros and screenshot sessions."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from domain.exceptions import InvalidURLError
from domain.models import OCRDocument


class MacroActionType(StrEnum):
    """Supported, declarative browser operations."""

    GOTO = "goto"
    CLICK = "click"
    FILL = "fill"
    PRESS = "press"
    WAIT = "wait"
    SCROLL = "scroll"
    SCREENSHOT = "screenshot"


@dataclass(frozen=True, slots=True)
class MacroAction:
    """One validated operation in a browser macro."""

    action: MacroActionType
    selector: str | None = None
    value: str | int | float | None = None
    name: str | None = None
    duration_ms: int = 0
    full_page: bool = True

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> MacroAction:
        """Build and validate an action from JSON-compatible data."""
        try:
            action_type = MacroActionType(str(raw["action"]).strip().lower())
        except (KeyError, ValueError) as exc:
            supported = ", ".join(item.value for item in MacroActionType)
            raise ValueError(f"Action invalide. Actions disponibles : {supported}.") from exc

        action = cls(
            action=action_type,
            selector=_optional_text(raw.get("selector")),
            value=raw.get("value"),
            name=_optional_text(raw.get("name")),
            duration_ms=int(raw.get("duration_ms", 0)),
            full_page=bool(raw.get("full_page", True)),
        )
        action.validate()
        return action

    def validate(self) -> None:
        """Enforce the fields required by each action type."""
        if self.duration_ms < 0:
            raise ValueError("La durée d'une action ne peut pas être négative.")
        if self.action in {MacroActionType.CLICK, MacroActionType.FILL, MacroActionType.PRESS}:
            if not self.selector:
                raise ValueError(f"L'action '{self.action.value}' exige un sélecteur.")
        if self.action in {MacroActionType.FILL, MacroActionType.PRESS, MacroActionType.GOTO}:
            if self.value is None or not str(self.value).strip():
                raise ValueError(f"L'action '{self.action.value}' exige une valeur.")
        if self.action == MacroActionType.SCROLL:
            try:
                int(self.value if self.value is not None else 0)
            except (TypeError, ValueError) as exc:
                raise ValueError("L'action 'scroll' exige une valeur entière.") from exc


@dataclass(frozen=True, slots=True)
class MacroDefinition:
    """Complete macro settings independent from Streamlit and Playwright."""

    name: str
    start_url: str
    actions: tuple[MacroAction, ...]
    headless: bool = True
    timeout_seconds: int = 60
    viewport_width: int = 1440
    viewport_height: int = 900
    persist_session: bool = True
    perform_ocr: bool = False

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> MacroDefinition:
        """Build a macro from decoded JSON."""
        actions_raw = raw.get("actions", [])
        if not isinstance(actions_raw, list):
            raise ValueError("'actions' doit être une liste JSON.")
        macro = cls(
            name=str(raw.get("name", "macro")).strip(),
            start_url=str(raw.get("start_url", "")).strip(),
            actions=tuple(MacroAction.from_dict(item) for item in actions_raw),
            headless=bool(raw.get("headless", True)),
            timeout_seconds=int(raw.get("timeout_seconds", 60)),
            viewport_width=int(raw.get("viewport_width", 1440)),
            viewport_height=int(raw.get("viewport_height", 900)),
            persist_session=bool(raw.get("persist_session", True)),
            perform_ocr=bool(raw.get("perform_ocr", False)),
        )
        macro.validate()
        return macro

    def validate(self) -> None:
        """Validate URL, identifiers and execution limits."""
        parsed = urlparse(self.start_url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise InvalidURLError("La macro exige une URL HTTP ou HTTPS complète.")
        if not self.name:
            raise ValueError("Le nom de la macro est obligatoire.")
        if self.timeout_seconds < 1 or self.timeout_seconds > 3600:
            raise ValueError("Le délai maximal doit être compris entre 1 et 3600 secondes.")
        if self.viewport_width < 320 or self.viewport_height < 240:
            raise ValueError("La taille de fenêtre est trop petite.")

    @property
    def safe_name(self) -> str:
        """Return a filesystem-safe identifier."""
        value = re.sub(r"[^a-zA-Z0-9_-]+", "_", self.name.strip()).strip("_")
        return value or "macro"

    def to_dict(self) -> dict[str, Any]:
        """Serialize the macro for persistence."""
        return {
            "name": self.name,
            "start_url": self.start_url,
            "headless": self.headless,
            "timeout_seconds": self.timeout_seconds,
            "viewport_width": self.viewport_width,
            "viewport_height": self.viewport_height,
            "persist_session": self.persist_session,
            "perform_ocr": self.perform_ocr,
            "actions": [
                {
                    key: value
                    for key, value in {
                        "action": action.action.value,
                        "selector": action.selector,
                        "value": action.value,
                        "name": action.name,
                        "duration_ms": action.duration_ms,
                        "full_page": action.full_page,
                    }.items()
                    if value is not None
                }
                for action in self.actions
            ],
        }


@dataclass(frozen=True, slots=True)
class MacroRunResult:
    """Artifacts produced by one macro execution."""

    macro_name: str
    screenshots: tuple[Path, ...]
    session_directory: Path
    duration_seconds: float
    stopped_by_user: bool = False
    document: OCRDocument | None = None


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None
