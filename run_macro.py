"""Command-line entry point used by schedulers and manual runs."""

from __future__ import annotations

import argparse
import logging
from dataclasses import replace
from pathlib import Path
from threading import Event

from application.macro_use_cases import MacroRepository, RunMacroUseCase
from domain.text_reconstruction import TextReconstructor
from services.macro_browser_service import MacroBrowserService
from services.ocr_service import OCRService

PROJECT_ROOT = Path(__file__).resolve().parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Exécuter une macro Playwright enregistrée.")
    parser.add_argument("--config", type=Path, required=True, help="Chemin du fichier JSON.")
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Forcer Chromium en arrière-plan.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    logs_directory = PROJECT_ROOT / "data"
    logs_directory.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[
            logging.FileHandler(logs_directory / "macro_runner.log", encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )

    repository = MacroRepository(args.config.parent)
    macro = repository.load(args.config)
    if args.headless:
        macro = replace(macro, headless=True)

    browser = MacroBrowserService(
        screenshots_directory=PROJECT_ROOT / "screenshots",
        profiles_directory=PROJECT_ROOT / "data" / "browser_profiles",
    )
    result = RunMacroUseCase(
        browser=browser,
        ocr=OCRService(),
        reconstructor=TextReconstructor(),
    ).execute(
        macro,
        Event(),
        lambda message, current, total: logging.info(
            "%s (%.0f/%.0f)", message, current, total
        ),
    )
    logging.info(
        "Macro terminée en %.1f s : %d capture(s) dans %s",
        result.duration_seconds,
        len(result.screenshots),
        result.session_directory,
    )
    if result.document:
        text_path = result.session_directory / "ocr.txt"
        text_path.write_text(result.document.text, encoding="utf-8")
        logging.info("Texte OCR enregistré dans %s", text_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
