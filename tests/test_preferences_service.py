from services.preferences_service import PreferencesService


def test_preferences_round_trip(tmp_path) -> None:
    service = PreferencesService(tmp_path / "preferences.json")

    assert service.load_last_url() == "https://example.com"

    service.save_last_url("https://example.org/page")

    assert service.load_last_url() == "https://example.org/page"


def test_preferences_falls_back_when_file_is_invalid(tmp_path) -> None:
    path = tmp_path / "preferences.json"
    path.write_text("{invalid", encoding="utf-8")

    assert PreferencesService(path).load_last_url("https://fallback.test") == (
        "https://fallback.test"
    )

