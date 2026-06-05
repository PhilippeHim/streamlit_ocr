import pytest

from domain.macro_models import MacroActionType, MacroDefinition


def test_macro_definition_parses_supported_actions() -> None:
    macro = MacroDefinition.from_dict(
        {
            "name": "Mon jeu",
            "start_url": "https://example.com",
            "actions": [
                {"action": "click", "selector": "#next"},
                {"action": "wait", "duration_ms": 500},
                {"action": "screenshot", "name": "classement"},
            ],
        }
    )

    assert macro.safe_name == "Mon_jeu"
    assert macro.actions[0].action == MacroActionType.CLICK
    assert macro.actions[2].full_page is True


def test_macro_rejects_click_without_selector() -> None:
    with pytest.raises(ValueError, match="sélecteur"):
        MacroDefinition.from_dict(
            {
                "name": "invalid",
                "start_url": "https://example.com",
                "actions": [{"action": "click"}],
            }
        )


def test_macro_rejects_unknown_action() -> None:
    with pytest.raises(ValueError, match="Action invalide"):
        MacroDefinition.from_dict(
            {
                "name": "invalid",
                "start_url": "https://example.com",
                "actions": [{"action": "execute_python", "value": "print('no')"}],
            }
        )

