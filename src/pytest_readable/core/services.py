# Copyright 2026 José Luis López López Prieto and contributors
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

"""High-level orchestration helpers for exporting readable suites."""

from pathlib import Path

from pytest_readable.core.exporters import render_csv, write_output
from pytest_readable.core.models import ReadableSuite
from pytest_readable.core.renderer import render_markdown


def export_suite(suite: ReadableSuite, out_format: str, output_path: Path, language: str) -> Path:
    """Export the suite in the requested format and persist to disk."""
    if out_format == "markdown":
        content = render_markdown(suite, language)
    elif out_format == "csv":
        content = render_csv(suite, language)
    else:
        raise ValueError(f"Unsupported output format: {out_format}")

    return write_output(output_path, content)
