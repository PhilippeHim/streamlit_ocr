"""OpenCV preprocessing and Tesseract OCR adapter."""

from __future__ import annotations

import logging
import shutil
from pathlib import Path

import cv2
import pytesseract
from pytesseract import Output

from application.ports import ProgressCallback
from domain.exceptions import OCRProcessingError
from domain.models import OCRFrame, OCRLine

LOGGER = logging.getLogger(__name__)


class OCRService:
    """Recognize positioned text lines in extracted images."""

    def __init__(self, language: str = "fra+eng", minimum_confidence: float = 35.0) -> None:
        self.language = language
        self.minimum_confidence = minimum_confidence

    def recognize_frames(
        self,
        frames: list[tuple[Path, float]],
        progress: ProgressCallback,
    ) -> tuple[OCRFrame, ...]:
        """OCR every frame and retain text line coordinates."""
        if not shutil.which("tesseract"):
            raise OCRProcessingError(
                "Tesseract est introuvable. Installez-le via l'environnement Conda."
            )

        results: list[OCRFrame] = []
        total = float(len(frames))
        for index, (image_path, timestamp) in enumerate(frames, start=1):
            progress(f"OCR de l'image {index}/{len(frames)}", float(index - 1), total)
            image = cv2.imread(str(image_path))
            if image is None:
                raise OCRProcessingError(f"Impossible de lire {image_path}.")
            processed = self._preprocess(image)
            lines = self._extract_lines(processed)
            results.append(
                OCRFrame(
                    image_path=image_path,
                    timestamp_seconds=timestamp,
                    lines=tuple(lines),
                )
            )
        progress("OCR terminé", total, total)
        LOGGER.info("OCR completed for %d frames", len(results))
        return tuple(results)

    @staticmethod
    def _preprocess(image):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        enlarged = cv2.resize(gray, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_CUBIC)
        return cv2.threshold(enlarged, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

    def _extract_lines(self, image) -> list[OCRLine]:
        try:
            data = pytesseract.image_to_data(
                image,
                lang=self.language,
                config="--oem 3 --psm 6",
                output_type=Output.DICT,
            )
        except pytesseract.TesseractError as exc:
            if self.language != "eng":
                LOGGER.warning("OCR language %s unavailable, falling back to eng", self.language)
                data = pytesseract.image_to_data(
                    image,
                    lang="eng",
                    config="--oem 3 --psm 6",
                    output_type=Output.DICT,
                )
            else:
                raise OCRProcessingError(f"Tesseract a échoué: {exc}") from exc

        height = max(1, image.shape[0])
        grouped: dict[tuple[int, int, int], list[tuple[str, float, int]]] = {}
        for index, raw_text in enumerate(data["text"]):
            text = raw_text.strip()
            confidence = float(data["conf"][index])
            if not text or confidence < self.minimum_confidence:
                continue
            key = (
                int(data["block_num"][index]),
                int(data["par_num"][index]),
                int(data["line_num"][index]),
            )
            grouped.setdefault(key, []).append((text, confidence, int(data["top"][index])))

        lines: list[OCRLine] = []
        for words in grouped.values():
            text = " ".join(word for word, _, _ in words)
            confidence = sum(score for _, score, _ in words) / len(words)
            y_ratio = min(top for _, _, top in words) / height
            lines.append(OCRLine(text=text, y_ratio=y_ratio, confidence=confidence))
        return lines

