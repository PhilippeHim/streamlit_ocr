from pathlib import Path
from threading import Event

from application.macro_use_cases import RunMacroUseCase
from domain.macro_models import MacroDefinition, MacroRunResult
from domain.models import OCRFrame, OCRLine
from domain.text_reconstruction import TextReconstructor


class FakeBrowser:
    def run_macro(self, macro, stop_event, progress):
        return MacroRunResult(
            macro_name=macro.name,
            screenshots=(Path("capture.png"),),
            session_directory=Path("session"),
            duration_seconds=1.0,
        )


class FakeOCR:
    def recognize_frames(self, frames, progress):
        return (
            OCRFrame(
                image_path=frames[0][0],
                timestamp_seconds=0.0,
                lines=(OCRLine("Texte reconnu", 0.5, 95.0),),
            ),
        )


def test_macro_ocr_builds_document() -> None:
    macro = MacroDefinition.from_dict(
        {
            "name": "capture",
            "start_url": "https://example.com",
            "perform_ocr": True,
            "actions": [{"action": "screenshot", "name": "page"}],
        }
    )
    use_case = RunMacroUseCase(FakeBrowser(), FakeOCR(), TextReconstructor())

    result = use_case.execute(macro, Event(), lambda *args: None)

    assert result.document is not None
    assert result.document.text == "Texte reconnu"
    assert result.document.source_url == "https://example.com"


def test_macro_without_ocr_keeps_document_empty() -> None:
    macro = MacroDefinition.from_dict(
        {
            "name": "capture",
            "start_url": "https://example.com",
            "perform_ocr": False,
            "actions": [{"action": "screenshot", "name": "page"}],
        }
    )
    use_case = RunMacroUseCase(FakeBrowser(), FakeOCR(), TextReconstructor())

    result = use_case.execute(macro, Event(), lambda *args: None)

    assert result.document is None

