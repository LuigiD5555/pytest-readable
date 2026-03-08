"""File exporter helpers for readable suite content."""

import csv
import io
from pathlib import Path

from pytest_readable.core.models import ReadableSuite
from pytest_readable.language_registry import get_language_pack


def render_csv(suite: ReadableSuite, language: str) -> str:
    """Serialize readable cases into CSV rows with a localized header."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(list(get_language_pack(language).csv_headers))

    for case in suite.cases:
        writer.writerow(
            [
                case.module_path,
                case.class_name,
                case.display_name,
                case.what,
                " | ".join(case.steps),
                case.status,
                case.nodeid,
            ]
        )
    return output.getvalue()


def write_output(path: Path, content: str) -> Path:
    """Ensure the output directory exists and write the given text."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path
