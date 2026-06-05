"""TXT, Markdown and PDF export adapter."""

from __future__ import annotations

from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from domain.exceptions import ExportError
from domain.models import OCRDocument


class ExportService:
    """Serialize OCR documents into downloadable formats."""

    def to_txt(self, document: OCRDocument) -> bytes:
        return document.text.encode("utf-8")

    def to_markdown(self, document: OCRDocument) -> bytes:
        content = (
            f"# {document.title}\n\n"
            f"Source : {document.source_url}\n\n"
            f"{document.text}\n"
        )
        return content.encode("utf-8")

    def to_pdf(self, document: OCRDocument) -> bytes:
        buffer = BytesIO()
        try:
            pdf = SimpleDocTemplate(
                buffer,
                pagesize=A4,
                leftMargin=18 * mm,
                rightMargin=18 * mm,
                topMargin=18 * mm,
                bottomMargin=18 * mm,
                title=document.title,
            )
            styles = getSampleStyleSheet()
            story = [
                Paragraph(escape(document.title), styles["Title"]),
                Paragraph(f"Source : {escape(document.source_url)}", styles["Italic"]),
                Spacer(1, 8 * mm),
            ]
            paragraphs = document.text.split("\n") or [""]
            for paragraph in paragraphs:
                story.append(Paragraph(escape(paragraph) or " ", styles["BodyText"]))
                story.append(Spacer(1, 2 * mm))
            pdf.build(story)
        except Exception as exc:
            raise ExportError(f"La génération du PDF a échoué: {exc}") from exc
        return buffer.getvalue()

