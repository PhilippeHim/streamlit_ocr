"""TXT, Markdown and CSV export adapter."""

from __future__ import annotations

import csv
from io import StringIO

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

    def to_csv(self, document: OCRDocument) -> bytes:
        """Serialize reconstructed lines as an Excel-compatible UTF-8 CSV."""
        buffer = StringIO(newline="")
        try:
            writer = csv.writer(
                buffer,
                delimiter=";",
                quotechar='"',
                quoting=csv.QUOTE_MINIMAL,
                lineterminator="\r\n",
            )
            writer.writerow(
                ["titre", "source", "date_creation", "numero_ligne", "texte"]
            )
            created_at = document.created_at.isoformat(sep=" ", timespec="seconds")
            for index, line in enumerate(document.text.splitlines() or [""], start=1):
                writer.writerow(
                    [
                        document.title,
                        document.source_url,
                        created_at,
                        index,
                        line,
                    ]
                )
        except (csv.Error, ValueError) as exc:
            raise ExportError(f"La génération du fichier CSV a échoué : {exc}") from exc

        # utf-8-sig adds a BOM so desktop Excel detects accented text correctly.
        return buffer.getvalue().encode("utf-8-sig")

