from pathlib import Path

from domain.models import OCRFrame, OCRLine
from domain.text_reconstruction import TextReconstructor


def make_frame(index: int, values: list[tuple[str, float]]) -> OCRFrame:
    return OCRFrame(
        image_path=Path(f"frame-{index}.png"),
        timestamp_seconds=float(index),
        lines=tuple(OCRLine(text, y, 90.0) for text, y in values),
    )


def test_reconstruct_removes_overlap_and_repeated_chrome() -> None:
    frames = (
        make_frame(1, [("Menu", 0.02), ("Titre", 0.2), ("Première ligne", 0.4)]),
        make_frame(
            2,
            [("Menu", 0.02), ("Première ligne", 0.2), ("Deuxième ligne", 0.4)],
        ),
        make_frame(3, [("Menu", 0.02), ("Deuxième ligne", 0.2), ("Conclusion", 0.4)]),
    )

    result = TextReconstructor().reconstruct(frames)

    assert result == "Titre\nPremière ligne\nDeuxième ligne\nConclusion"

