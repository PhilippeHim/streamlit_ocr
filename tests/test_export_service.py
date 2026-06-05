from domain.models import OCRDocument
from services.export_service import ExportService


def test_exports_return_expected_formats() -> None:
    document = OCRDocument(
        title="Test",
        source_url="https://example.com",
        text="Bonjour\nMonde",
        frames=(),
    )
    service = ExportService()

    assert service.to_txt(document) == b"Bonjour\nMonde"
    assert b"# Test" in service.to_markdown(document)
    assert service.to_pdf(document).startswith(b"%PDF")

