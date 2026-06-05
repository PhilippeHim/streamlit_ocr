"""Playwright adapter for declarative navigation macros."""

from __future__ import annotations

import logging
import os
import re
import time
from datetime import datetime
from pathlib import Path
from threading import Event

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Page, sync_playwright

from application.ports import ProgressCallback
from domain.exceptions import CaptureError
from domain.macro_models import MacroAction, MacroActionType, MacroDefinition, MacroRunResult

LOGGER = logging.getLogger(__name__)
ENV_PATTERN = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")


class MacroBrowserService:
    """Run validated browser operations and persist screenshots/session state."""

    def __init__(self, screenshots_directory: Path, profiles_directory: Path) -> None:
        self.screenshots_directory = screenshots_directory
        self.profiles_directory = profiles_directory
        self.screenshots_directory.mkdir(parents=True, exist_ok=True)
        self.profiles_directory.mkdir(parents=True, exist_ok=True)

    def run_macro(
        self,
        macro: MacroDefinition,
        stop_event: Event,
        progress: ProgressCallback,
    ) -> MacroRunResult:
        """Execute a macro in Chromium, optionally reusing its authenticated session."""
        started_at = time.monotonic()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        session_directory = self.screenshots_directory / "macros" / macro.safe_name / timestamp
        session_directory.mkdir(parents=True, exist_ok=True)
        profile_path = self.profiles_directory / f"{macro.safe_name}.json"
        screenshots: list[Path] = []
        stopped_by_user = False
        total_steps = float(max(1, len(macro.actions) + 1))

        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=macro.headless)
                context_options: dict[str, object] = {
                    "viewport": {
                        "width": macro.viewport_width,
                        "height": macro.viewport_height,
                    }
                }
                if macro.persist_session and profile_path.exists():
                    context_options["storage_state"] = str(profile_path)
                context = browser.new_context(**context_options)
                context.set_default_timeout(macro.timeout_seconds * 1000)
                page = context.new_page()

                progress("Ouverture de la page de départ", 0.0, total_steps)
                page.goto(macro.start_url, wait_until="domcontentloaded")

                for index, action in enumerate(macro.actions, start=1):
                    if stop_event.is_set():
                        stopped_by_user = True
                        break
                    progress(
                        f"Étape {index}/{len(macro.actions)} : {action.action.value}",
                        float(index),
                        total_steps,
                    )
                    try:
                        screenshot = self._execute_action(
                            page,
                            action,
                            session_directory,
                            len(screenshots) + 1,
                        )
                    except PlaywrightError as exc:
                        raise CaptureError(
                            self._action_error_message(index, action, page, exc)
                        ) from exc
                    if screenshot:
                        screenshots.append(screenshot)

                if macro.persist_session:
                    context.storage_state(path=str(profile_path))
                context.close()
                browser.close()
        except PlaywrightError as exc:
            raise CaptureError(f"La macro Playwright a échoué : {exc}") from exc

        duration = time.monotonic() - started_at
        progress("Macro terminée", total_steps, total_steps)
        LOGGER.info("Macro %s completed with %d screenshots", macro.name, len(screenshots))
        return MacroRunResult(
            macro_name=macro.name,
            screenshots=tuple(screenshots),
            session_directory=session_directory,
            duration_seconds=duration,
            stopped_by_user=stopped_by_user,
        )

    def _execute_action(
        self,
        page: Page,
        action: MacroAction,
        session_directory: Path,
        screenshot_index: int,
    ) -> Path | None:
        """Map one domain action to Playwright."""
        if action.action == MacroActionType.GOTO:
            page.goto(self._expand(str(action.value)), wait_until="domcontentloaded")
        elif action.action == MacroActionType.CLICK:
            locator = page.locator(action.selector or "")
            locator.wait_for(state="visible")
            locator.click()
        elif action.action == MacroActionType.FILL:
            page.locator(action.selector or "").fill(self._expand(str(action.value)))
        elif action.action == MacroActionType.PRESS:
            page.locator(action.selector or "").press(self._expand(str(action.value)))
        elif action.action == MacroActionType.WAIT:
            duration = action.duration_ms or int(action.value or 1000)
            page.wait_for_timeout(duration)
        elif action.action == MacroActionType.SCROLL:
            page.evaluate("(distance) => window.scrollBy(0, distance)", int(action.value or 0))
        elif action.action == MacroActionType.SCREENSHOT:
            filename = self._screenshot_name(action.name, screenshot_index)
            destination = session_directory / filename
            page.screenshot(path=str(destination), full_page=action.full_page)
            return destination

        if action.duration_ms:
            page.wait_for_timeout(action.duration_ms)
        return None

    @staticmethod
    def _action_error_message(
        index: int,
        action: MacroAction,
        page: Page,
        error: PlaywrightError,
    ) -> str:
        """Return an actionable error instead of the raw Playwright call log."""
        selector = f" avec le sélecteur {action.selector!r}" if action.selector else ""
        if page.is_closed() or "Target page, context or browser has been closed" in str(error):
            return (
                f"Étape {index} ({action.action.value}) interrompue : la fenêtre Chromium "
                "a été fermée. Laissez-la ouverte jusqu'à la fin de la macro."
            )
        try:
            current_url = page.url
        except PlaywrightError:
            current_url = "indisponible"
        return (
            f"Étape {index} ({action.action.value}) impossible{selector} sur "
            f"{current_url}. Vérifiez que l'élément existe et que son sélecteur correspond "
            "à la page actuelle."
        )

    @staticmethod
    def _expand(value: str) -> str:
        """Resolve ${VARIABLE} placeholders without storing secrets in JSON."""
        def replace(match: re.Match[str]) -> str:
            variable = match.group(1)
            if variable not in os.environ:
                raise ValueError(f"La variable d'environnement {variable} est absente.")
            return os.environ[variable]

        return ENV_PATTERN.sub(replace, value)

    @staticmethod
    def _screenshot_name(name: str | None, index: int) -> str:
        stem = re.sub(r"[^a-zA-Z0-9_-]+", "_", name or f"capture_{index:03d}").strip("_")
        return f"{stem or f'capture_{index:03d}'}.png"
