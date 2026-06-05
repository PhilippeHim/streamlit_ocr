from pathlib import Path

from domain.macro_models import MacroAction, MacroActionType
from services.macro_browser_service import MacroBrowserService


class ClosedPage:
    def is_closed(self) -> bool:
        return True


def test_closed_browser_error_is_actionable() -> None:
    action = MacroAction(
        action=MacroActionType.CLICK,
        selector="a[href='/page-2']",
    )

    message = MacroBrowserService._action_error_message(
        3,
        action,
        ClosedPage(),  # type: ignore[arg-type]
        Exception("Target page, context or browser has been closed"),  # type: ignore[arg-type]
    )

    assert "fenêtre Chromium a été fermée" in message
    assert "Étape 3" in message


def test_screenshot_name_is_sanitized() -> None:
    assert MacroBrowserService._screenshot_name("Page numéro 2", 1) == "Page_num_ro_2.png"
