# Copyright 2026 LuigiD5555
# Licensed under the MIT License
# See LICENSE file for details.

"""Dataclasses that capture the readable view of pytest tests."""

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ReadableTestCase:
    """Describes one pytest test plus its readable metadata."""

    nodeid: str
    module_path: str
    class_name: str
    function_name: str
    display_name: str
    language: str = ""
    what: str = ""
    steps: list[str] = field(default_factory=list)
    criteria: list[str] = field(default_factory=list)
    markers: list[str] = field(default_factory=list)
    status: str = "collected"
    error_message: str = ""


@dataclass
class ReadableSuite:
    """Aggregated tests for a given pytest root directory."""

    rootdir: Path
    language: str
    cases: list[ReadableTestCase] = field(default_factory=list)
    deselected: int = 0
    warnings: int = 0

    def counts(self) -> dict[str, int]:
        """Return a count of cases by status plus total."""
        counts: dict[str, int] = {}
        for case in self.cases:
            counts[case.status] = counts.get(case.status, 0) + 1
        counts["total"] = len(self.cases)
        return counts
