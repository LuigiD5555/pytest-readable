# Copyright 2026 José Luis López López Prieto and contributors
# Licensed under the Apache License, Version 2.0
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


@dataclass
class ReadableSuite:
    """Aggregated tests for a given pytest root directory."""

    rootdir: Path
    language: str
    cases: list[ReadableTestCase] = field(default_factory=list)

    def counts(self) -> dict[str, int]:
        """Return a count of cases by status plus total."""
        counts: dict[str, int] = {}
        for case in self.cases:
            counts[case.status] = counts.get(case.status, 0) + 1
        counts["total"] = len(self.cases)
        return counts
