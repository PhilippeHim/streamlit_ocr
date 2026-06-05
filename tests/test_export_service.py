import csv
from io import StringIO
from pathlib import Path

from domain.models import OCRDocument, OCRFrame, OCRLine
from services.export_service import ExportService


def test_exports_return_expected_formats() -> None:
    document = OCRDocument(
        title="Test",
        source_url="https://example.com",
        text='Bonjour; "Monde"\nDeuxième ligne',
        frames=(
            OCRFrame(
                image_path=Path("frame.png"),
                timestamp_seconds=1.5,
                lines=(OCRLine(text="Bonjour", y_ratio=0.2, confidence=92.5),),
            ),
        ),
    )
    service = ExportService()

    assert service.to_txt(document) == 'Bonjour; "Monde"\nDeuxième ligne'.encode()
    assert b"# Test" in service.to_markdown(document)
    csv_content = service.to_csv(document)
    assert csv_content.startswith(b"\xef\xbb\xbf")
    rows = list(
        csv.reader(
            StringIO(csv_content.decode("utf-8-sig")),
            delimiter=";",
        )
    )
    assert rows[0] == ["titre", "source", "date_creation", "numero_ligne", "texte"]
    assert rows[1][3:] == ["1", 'Bonjour; "Monde"']
    assert rows[2][3:] == ["2", "Deuxième ligne"]
