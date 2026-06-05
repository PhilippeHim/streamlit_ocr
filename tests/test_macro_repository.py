import json

from application.macro_use_cases import MacroRepository
from domain.macro_models import MacroDefinition


def test_repository_round_trip(tmp_path) -> None:
    repository = MacroRepository(tmp_path)
    macro = MacroDefinition.from_dict(
        {
            "name": "captures test",
            "start_url": "https://example.com",
            "headless": False,
            "actions": [{"action": "screenshot", "name": "accueil"}],
        }
    )

    path = repository.save(macro)
    restored = repository.load(path)

    assert path.name == "captures_test.json"
    assert restored == macro
    assert json.loads(path.read_text(encoding="utf-8"))["actions"][0]["name"] == "accueil"

