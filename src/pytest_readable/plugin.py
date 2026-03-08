"""Pytest plugin entry point that produces readable summaries and exports."""

from pathlib import Path

from pytest_readable.core.parser import build_suite_from_items, detect_language_from_decorators
from pytest_readable.core.renderer import render_summary_text, render_tree_text
from pytest_readable.core.services import export_suite
from pytest_readable.i18n import get_i18n
from pytest_readable.language_registry import get_language_pack, supported_languages


STATUS_MAP = {
    "passed": "passed",
    "failed": "failed",
    "skipped": "skipped",
}


class ReadableRuntimePlugin:
    """Handles pytest hooks that produce readable output and exports."""

    def __init__(self, config):
        self.config = config
        self.suite = None
        self.i18n = None
        self.rendered_in_collect_only = False

    def _enabled(self) -> bool:
        """Return True when any readable flag was requested."""
        return any(
            [
                self.config.getoption("readable"),
                self.config.getoption("readable_tree"),
                self.config.getoption("readable_docs"),
            ]
        )

    def _verbosity(self) -> int:
        """Normalize pytest verbosity level for conditional output."""
        value = getattr(self.config.option, "verbose", 0)
        return int(value or 0)

    def _ensure_suite(self, items):
        """Build the readable suite once per session from collected items."""
        if self.suite is not None:
            return

        preferred_lang = self.config.getoption("readable_lang")
        if preferred_lang == "auto":
            detected = detect_language_from_decorators(Path(self.config.rootpath))
            if detected is not None:
                preferred_lang = detected

        self.i18n = get_i18n(preferred_lang)
        self.suite = build_suite_from_items(items, Path(self.config.rootpath), self.i18n)

    def _line_style(self, line: str) -> dict[str, bool]:
        """Return pytest terminal markup flags for a rendered summary line."""
        normalized = line.strip()
        what_prefixes = tuple(f"{get_language_pack(code).what_label}:" for code in supported_languages())
        if normalized.startswith(what_prefixes):
            return {"yellow": True}
        for code in supported_languages():
            status_labels = get_language_pack(code).status_labels
            if normalized.startswith(f"- [{status_labels['passed']}]") or normalized.startswith(
                f"- {status_labels['passed']}:"
            ):
                return {"green": True}
            if normalized.startswith(f"- [{status_labels['failed']}]") or normalized.startswith(
                f"- {status_labels['failed']}:"
            ):
                return {"red": True}
            if normalized.startswith(f"- [{status_labels['error']}]") or normalized.startswith(
                f"- {status_labels['error']}:"
            ):
                return {"red": True}
            if normalized.startswith(f"- [{status_labels['skipped']}]") or normalized.startswith(
                f"- {status_labels['skipped']}:"
            ):
                return {"yellow": True}
        return {}

    def _print_to_terminal(self, terminal_reporter, text: str) -> None:
        """Emit readable text through the terminal reporter with optional color."""
        if not text.strip():
            return
        terminal_reporter.write_line("")
        for line in text.splitlines():
            terminal_reporter.write_line(line, **self._line_style(line))

    def _export_if_requested(self, terminal_reporter):
        """Export readable docs after summary if the flag is enabled."""
        if not self.config.getoption("readable_docs"):
            return
        if self.suite is None or self.i18n is None:
            return

        out_format = self.config.getoption("readable_format")
        output = self.config.getoption("readable_out")
        if output:
            out_path = Path(output)
        else:
            ext = "md" if out_format == "markdown" else "csv"
            out_path = Path("docs") / f"tests-readable.{ext}"

        written = export_suite(self.suite, out_format, out_path, self.i18n.language)
        terminal_reporter.write_line(f"readable docs exported: {written}")

    def pytest_collection_finish(self, session):
        if not self._enabled():
            return

        self._ensure_suite(session.items)

        if self.config.getoption("collectonly") and self.suite is not None:
            terminal_reporter = self.config.pluginmanager.get_plugin("terminalreporter")
            if terminal_reporter is None:
                return

            include_steps = self.config.getoption("readable_include_steps") or self._verbosity() >= 2
            if self.config.getoption("readable_tree"):
                text = render_tree_text(self.suite, include_steps=include_steps)
            else:
                text = render_summary_text(
                    self.suite,
                    self.i18n.language,
                    verbose=self._verbosity(),
                    include_steps=include_steps,
                )
            self._print_to_terminal(terminal_reporter, text)
            self._export_if_requested(terminal_reporter)
            self.rendered_in_collect_only = True

    def pytest_runtest_logreport(self, report):
        if not self._enabled() or self.suite is None:
            return

        if report.when == "call":
            status = STATUS_MAP.get(report.outcome, report.outcome)
        elif report.when == "setup" and report.skipped:
            status = "skipped"
        else:
            return

        for case in self.suite.cases:
            if case.nodeid == report.nodeid:
                case.status = status
                break

    def pytest_terminal_summary(self, terminalreporter):
        if not self._enabled():
            return

        if self.config.getoption("collectonly") and self.rendered_in_collect_only:
            return

        if self.suite is None:
            return

        include_steps = self.config.getoption("readable_include_steps") or self._verbosity() >= 2
        if self.config.getoption("readable_tree"):
            text = render_tree_text(self.suite, include_steps=include_steps)
        else:
            text = render_summary_text(
                self.suite,
                self.i18n.language,
                verbose=self._verbosity(),
                include_steps=include_steps,
            )

        self._print_to_terminal(terminalreporter, text)
        self._export_if_requested(terminalreporter)


def pytest_addoption(parser):
    """Register the CLI flags that control readable output and exports."""
    group = parser.getgroup("readable")
    group.addoption("--readable", action="store_true", help="Print a readable pytest summary")
    group.addoption("--readable-tree", action="store_true", help="Print the collected tests as a hierarchy")
    group.addoption(
        "--readable-docs",
        action="store_true",
        help="Export readable docs to markdown or csv",
    )
    group.addoption(
        "--readable-out",
        action="store",
        default="",
        metavar="PATH",
        help="Output path for readable docs",
    )
    group.addoption(
        "--readable-format",
        action="store",
        choices=["markdown", "csv"],
        default="markdown",
        help="Format for readable docs export",
    )
    group.addoption(
        "--readable-lang",
        action="store",
        choices=["auto", *supported_languages()],
        default="auto",
        help="Language for readable output",
    )
    group.addoption(
        "--readable-include-steps",
        action="store_true",
        help="Include documented steps in readable output",
    )


def pytest_configure(config):
    """Register the runtime plugin once pytest is configuring."""
    plugin = ReadableRuntimePlugin(config)
    config.pluginmanager.register(plugin, "pytest_readable_runtime")
