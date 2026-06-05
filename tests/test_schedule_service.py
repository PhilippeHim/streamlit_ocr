import plistlib
from pathlib import Path

from services.schedule_service import ScheduleService


def test_create_macos_daily_schedule(tmp_path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    macro_path = project / "macro.json"
    macro_path.write_text("{}", encoding="utf-8")
    service = ScheduleService(project, Path("/conda/env/bin/python"))

    plist_path = service.create_macos_daily_schedule(
        macro_path,
        "Capture jeu",
        hour=4,
        minute=15,
    )

    with plist_path.open("rb") as stream:
        payload = plistlib.load(stream)

    assert payload["StartCalendarInterval"] == {"Hour": 4, "Minute": 15}
    assert payload["ProgramArguments"][0] == "/conda/env/bin/python"
    assert payload["ProgramArguments"][-1] == "--headless"

