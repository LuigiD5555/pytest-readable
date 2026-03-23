# Copyright 2026 LuigiD5555
# Licensed under the MIT License
# See LICENSE file for details.

"""Pytest plugin entry point that produces readable summaries and exports."""

from pathlib import Path

from pytest_readable.core.parser import build_suite_from_items, detect_language_from_decorators
from pytest_readable.core.path_strategies import PathStrategyFactory
from pytest_readable.core.renderer import render_summary_text, render_tree_text
from pytest_readable.core.services import export_suite
from pytest_readable.i18n import get_i18n
from pytest_readable.language_registry import get_language_pack, supported_languages


STATUS_MAP = {
    "passed": "passed",
    "failed": "failed",
    "skipped": "skipped",
    "xfailed": "xfailed",
    "xpassed": "xpassed",
}


class ReadableRuntimePlugin:
    """Handles pytest hooks that produce readable output and exports."""

    def __init__(self, config):
        """Initialize plugin configuration and runtime caches."""
        self.config = config
        self.suite = None
        self.i18n = None
        self.rendered_in_collect_only = False
        self._export_done = False
        self._deselected_count = 0
        self._warning_count = 0

    def _enabled(self) -> bool:
        """Return True when any readable flag was requested."""
        return any(
            [
                self.config.getoption("readable"),
                self.config.getoption("readable_detailed"),
                self.config.getoption("readable_verbose"),
                self.config.getoption("readable_tree"),
                self.config.getoption("readable_docs"),
                self._get_export_format() is not None,
            ]
        )

    def _summary_mode(self) -> str:
        """Return the active readable rendering mode."""
        if self.config.getoption("readable_verbose"):
            return "verbose"
        if self.config.getoption("readable") and self._verbosity() > 0:
            return "verbose"
        if self.config.getoption("readable_detailed"):
            return "detailed"
        if self.config.getoption("readable"):
            return "summary"
        return "off"

    def _verbosity(self) -> int:
        """Normalize pytest verbosity level for conditional output."""
        value = getattr(self.config.option, "verbose", 0)
        return int(value or 0)

    def _summary_verbosity(self) -> int:
        """Return the effective verbosity used by the readable summary renderer."""
        mode = self._summary_mode()
        if mode == "verbose":
            return 2
        if mode in {"summary", "detailed"}:
            return 1
        return self._verbosity()

    def _summary_include_what(self) -> bool:
        """Return True when the readable summary should include the case intention."""
        return self._summary_mode() in {"summary", "detailed", "verbose"}

    def _summary_include_steps(self) -> bool:
        """Return True when the readable summary should include full case details."""
        if self.config.getoption("readable_include_steps"):
            return True
        mode = self._summary_mode()
        if mode == "summary":
            return False
        if mode in {"detailed", "verbose"}:
            return True
        return self.config.getoption("readable_include_steps")

    def _render_summary(self) -> str:
        """Render the current readable summary according to the active mode."""
        summary_verbosity = self._summary_verbosity()
        include_what = self._summary_include_what()
        include_steps = self._summary_include_steps()
        include_display_name = self._summary_mode() in {"detailed", "verbose"}
        if self.config.getoption("readable_tree"):
            return render_tree_text(self.suite, include_steps=include_steps)
        return render_summary_text(
            self.suite,
            self.i18n.language,
            verbose=summary_verbosity,
            include_what=include_what,
            include_steps=include_steps,
            include_display_name=include_display_name,
        )

    def _suppress_native_pytest_output(self) -> bool:
        """Return True when pytest's own terminal output should stay hidden."""
        return self._summary_mode() in {"summary", "detailed"}

    def _ensure_suite(self, items):
        """Build the readable suite once per session from collected items."""
        if self.suite is not None:
            return

        requested_lang = self.config.getoption("readable_lang")
        preferred_lang = requested_lang
        if requested_lang == "auto":
            detected = detect_language_from_decorators(Path(self.config.rootpath))
            if detected is not None:
                preferred_lang = detected

        self.i18n = get_i18n(preferred_lang)
        project_root = Path(self.config.rootpath)
        path_mode = self.config.getoption("readable_path_mode")
        base_path = self.config.getoption("readable_base_path") or None
        factory = PathStrategyFactory(project_root=project_root, cwd=Path.cwd())
        path_strategy = factory.build(path_mode, base_path=base_path)
        self.suite = build_suite_from_items(
            items,
            project_root,
            self.i18n,
            preserve_case_language=requested_lang == "auto",
            path_strategy=path_strategy,
        )

    def _get_export_format(self) -> str | None:
        """Return the format requested through --export, if available."""
        try:
            return self.config.getoption("readable_export")
        except ValueError:
            return None

    def _line_style(self, line: str) -> dict[str, bool]:
        """Return pytest terminal markup flags for a rendered summary line."""
        normalized = line.strip()
        what_prefixes = tuple(f"{get_language_pack(code).what_label}:" for code in supported_languages())
        criteria_prefixes = tuple(f"{get_language_pack(code).criteria_label}:" for code in supported_languages())
        if normalized.startswith(what_prefixes):
            return {"yellow": True}
        if normalized.startswith(criteria_prefixes):
            return {"blue": True}
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
            if normalized.startswith(f"- [{status_labels['xfailed']}]") or normalized.startswith(
                f"- {status_labels['xfailed']}:"
            ):
                return {"yellow": True}
            if normalized.startswith(f"- [{status_labels['xpassed']}]") or normalized.startswith(
                f"- {status_labels['xpassed']}:"
            ):
                return {"green": True}
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
        if self._export_done:
            return
        export_format = self._get_export_format()
        if not self.config.getoption("readable_docs") and not export_format:
            return
        if self.suite is None or self.i18n is None:
            return

        out_format = export_format or self.config.getoption("readable_format")
        output = self.config.getoption("readable_out")
        if output:
            out_path = Path(output)
        else:
            ext = "md" if out_format == "markdown" else "csv"
            out_path = Path("docs") / f"tests-readable.{ext}"

        written = export_suite(self.suite, out_format, out_path, self.i18n.language)
        terminal_reporter.write_line(f"readable docs exported: {written}")
        self._export_done = True

    def _print_error_summary(self, terminal_reporter) -> None:
        """Print the short test summary info section when there are errors or failures."""
        has_errors = bool(terminal_reporter.stats.get("error"))
        has_failures = bool(terminal_reporter.stats.get("failed"))
        if not has_errors and not has_failures:
            return
        chars_needed = ""
        if has_errors:
            chars_needed += "E"
        if has_failures:
            chars_needed += "f"
        original_reportchars = terminal_reporter.reportchars
        terminal_reporter.reportchars = chars_needed
        try:
            terminal_reporter.short_test_summary()
        finally:
            terminal_reporter.reportchars = original_reportchars

    def pytest_collection_finish(self, session):
        """Build the readable suite after collection and optionally render during `--collect-only`."""
        if not self._enabled():
            return

        self._ensure_suite(session.items)

        if self.config.getoption("collectonly") and self.suite is not None:
            terminal_reporter = self.config.pluginmanager.get_plugin("terminalreporter")
            if terminal_reporter is None:
                return

            text = self._render_summary()
            self._print_to_terminal(terminal_reporter, text)
            self._export_if_requested(terminal_reporter)
            self.rendered_in_collect_only = True

    def pytest_sessionstart(self, session):
        """Silence pytest's native terminal noise for non-verbose readable modes."""
        del session
        if not self._suppress_native_pytest_output():
            return
        terminal_reporter = self.config.pluginmanager.get_plugin("terminalreporter")
        if terminal_reporter is None:
            return
        self.config.option.verbose = -2

    def pytest_deselected(self, items):
        """Track items removed by -k or -m filters."""
        self._deselected_count += len(items)

    def pytest_warning_recorded(self, warning_message, when, nodeid, location):
        """Count warnings emitted during the session."""
        del warning_message, when, nodeid, location
        self._warning_count += 1

    def pytest_runtest_logreport(self, report):
        """Map pytest reports to readable case statuses once each test call finishes."""
        if not self._enabled() or self.suite is None:
            return

        if report.when == "call":
            if hasattr(report, "wasxfail"):
                status = "xpassed" if report.outcome == "passed" else "xfailed"
            else:
                status = STATUS_MAP.get(report.outcome, report.outcome)
        elif report.when == "setup" and report.skipped:
            status = "skipped"
        elif report.when == "setup" and report.failed:
            status = "error"
        else:
            return

        error_message = ""
        if status in {"error", "failed"} and report.longrepr:
            longrepr = report.longrepr
            if hasattr(longrepr, "reprcrash") and longrepr.reprcrash:
                error_message = longrepr.reprcrash.message
            elif isinstance(longrepr, str):
                error_message = longrepr.strip().splitlines()[-1] if longrepr.strip() else ""

        for case in self.suite.cases:
            nid = report.nodeid
            if case.nodeid == nid or case.nodeid.endswith(nid) or nid.endswith(case.nodeid):
                case.status = status
                if error_message:
                    case.error_message = error_message
                break

    def pytest_report_teststatus(self, report, config):
        """Suppress pytest progress glyphs when readable owns the terminal output."""
        del config
        if not self._suppress_native_pytest_output():
            return None
        if report.when not in {"setup", "call", "teardown"}:
            return None
        if report.when == "setup" and report.skipped:
            return "skipped", "", ""
        return report.outcome, "", ""

    def pytest_terminal_summary(self, terminalreporter):
        """Show the readable summary when pytest completes, unless collect-only already printed it."""
        if not self._enabled():
            return

        if self.config.getoption("collectonly") and self.rendered_in_collect_only:
            return

        if self.suite is None:
            return
        if self._suppress_native_pytest_output():
            return
        self._print_to_terminal(terminalreporter, self._render_summary())

    def pytest_sessionfinish(self, session, exitstatus):
        """Export docs after execution, including runs that finish with test failures."""
        del exitstatus
        if not self._enabled() or self._export_done:
            return

        terminal_reporter = self.config.pluginmanager.get_plugin("terminalreporter")
        if terminal_reporter is None:
            return

        if self.suite is None:
            self._ensure_suite(getattr(session, "items", []))

        if self.suite is not None:
            self.suite.deselected = self._deselected_count
            self.suite.warnings = self._warning_count

        suppress = self._suppress_native_pytest_output()
        if self.suite is not None and not self.config.getoption("collectonly") and suppress:
            self._print_error_summary(terminal_reporter)
            self._print_to_terminal(terminal_reporter, self._render_summary())

        self._export_if_requested(terminal_reporter)


def pytest_addoption(parser):
    """Register CLI options that control readable output, tree view, and exports."""
    group = parser.getgroup("readable")
    group.addoption("--readable", action="store_true", help="Print a readable pytest summary")
    group.addoption(
        "--detailed",
        "--readable-detailed",
        dest="readable_detailed",
        action="store_true",
        help="Print a detailed readable summary with steps and pass conditions",
    )
    group.addoption(
        "--readable-verbose",
        action="store_true",
        help="Print an expanded readable summary with extra metadata context",
    )
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
    group.addoption(
        "--export",
        dest="readable_export",
        action="store",
        metavar="FORMAT",
        choices=["markdown", "csv"],
        default=None,
        help="Shortcut for --readable-docs and --readable-format=FORMAT",
    )
    group.addoption(
        "--path-mode",
        dest="readable_path_mode",
        action="store",
        choices=["auto", "root", "cwd", "explicit"],
        default="auto",
        help=(
            "How readable resolves display paths: "
            "'auto' uses cwd and falls back to project root (default), "
            "'root' always uses the project root, "
            "'cwd' uses the current working directory, "
            "'explicit' uses --base-path."
        ),
    )
    group.addoption(
        "--base-path",
        dest="readable_base_path",
        action="store",
        default="",
        metavar="PATH",
        help="Explicit base path for display paths when --path-mode=explicit.",
    )


def pytest_load_initial_conftests(early_config, parser, args):
    """Normalize readable shorthand flags before pytest parses the command line."""
    del early_config, parser
    if "--readable" not in args:
        return
    for index, value in enumerate(list(args)):
        if value == "-d":
            args[index] = "--readable-detailed"


def pytest_configure(config):
    """Register the runtime plugin once pytest is configuring."""
    readable_verbose_requested = config.getoption("readable_verbose") or (
        config.getoption("readable") and int(getattr(config.option, "verbose", 0) or 0) > 0
    )
    readable_mode_active = any(
        [
            config.getoption("readable"),
            config.getoption("readable_detailed"),
            config.getoption("readable_verbose"),
        ]
    )
    if readable_mode_active and not readable_verbose_requested:
        config.option.no_header = True
        config.option.no_summary = True
    plugin = ReadableRuntimePlugin(config)
    config.pluginmanager.register(plugin, "pytest_readable_runtime")
