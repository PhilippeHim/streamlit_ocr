"""Rules used to merge overlapping OCR frames into one document."""

from __future__ import annotations

import re
from collections import Counter
from difflib import SequenceMatcher

from domain.models import OCRFrame, OCRLine


class TextReconstructor:
    """Remove repeated page chrome and merge overlapping OCR lines."""

    def __init__(self, similarity_threshold: float = 0.91) -> None:
        self.similarity_threshold = similarity_threshold

    def reconstruct(self, frames: tuple[OCRFrame, ...]) -> str:
        """Return readable text while preserving the first occurrence order."""
        repeated_chrome = self._find_repeated_chrome(frames)
        merged: list[str] = []

        for frame in frames:
            frame_lines = [
                line.text.strip()
                for line in frame.lines
                if line.text.strip() and self._signature(line.text) not in repeated_chrome
            ]
            self._append_new_lines(merged, frame_lines)

        return "\n".join(merged).strip()

    def _find_repeated_chrome(self, frames: tuple[OCRFrame, ...]) -> set[str]:
        """Find stable lines near frame edges, usually headers or footers."""
        candidates: Counter[str] = Counter()
        for frame in frames:
            seen_in_frame: set[str] = set()
            for line in frame.lines:
                signature = self._signature(line.text)
                if signature and (line.y_ratio <= 0.15 or line.y_ratio >= 0.85):
                    seen_in_frame.add(signature)
            candidates.update(seen_in_frame)

        minimum_occurrences = max(2, len(frames) // 2)
        return {
            signature
            for signature, count in candidates.items()
            if count >= minimum_occurrences
        }

    def _append_new_lines(self, merged: list[str], incoming: list[str]) -> None:
        if not incoming:
            return

        overlap = self._overlap_size(merged, incoming)
        for line in incoming[overlap:]:
            if not self._is_recent_duplicate(line, merged):
                merged.append(line)

    def _overlap_size(self, existing: list[str], incoming: list[str]) -> int:
        max_size = min(len(existing), len(incoming), 40)
        for size in range(max_size, 0, -1):
            pairs = zip(existing[-size:], incoming[:size], strict=True)
            if all(self._similar(left, right) for left, right in pairs):
                return size
        return 0

    def _is_recent_duplicate(self, line: str, existing: list[str]) -> bool:
        return any(self._similar(line, previous) for previous in existing[-40:])

    def _similar(self, left: str, right: str) -> bool:
        left_signature = self._signature(left)
        right_signature = self._signature(right)
        if not left_signature or not right_signature:
            return left_signature == right_signature
        return (
            SequenceMatcher(None, left_signature, right_signature).ratio()
            >= self.similarity_threshold
        )

    @staticmethod
    def _signature(value: str) -> str:
        return re.sub(r"\W+", " ", value.casefold()).strip()

