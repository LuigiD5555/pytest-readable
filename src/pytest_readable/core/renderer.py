# Copyright 2026 LuigiD5555
# Licensed under the MIT License
# See LICENSE file for details.

"""Renderers that emit readable summaries, trees, and markup from suites."""

from datetime import datetime

from pytest_readable.core.models import ReadableSuite
from pytest_readable.language_registry import get_language_pack


def _status_label(status: str, language: str) -> str:
    """Return the localized label associated with `status` in `language`."""
    labels = get_language_pack(language).status_labels
    return labels.get(status, labels["unknown"])


def _render_case_lines(case, pack, include_what, include_steps, include_display_name) -> list[str]:
    """Emit the detail lines for a single test case."""
    lines: list[str] = []
    status_text = _status_label(case.status, pack.code)
    lines.append(f"- [{status_text}] {case.nodeid}")
    if include_display_name:
        lines.append(f"    {pack.display_name_label}: {case.display_name}")
    if (include_what or include_steps) and case.what:
        lines.append(f"    {pack.what_label}: {case.what}")
    if include_steps and case.steps:
        lines.append(f"    {pack.steps_label}:")
        for idx, step in enumerate(case.steps, 1):
            lines.append(f"      {idx}. {step}")
    if include_steps:
        lines.append(f"    {pack.criteria_label}:")
        if case.criteria:
            for idx, check in enumerate(case.criteria, 1):
                lines.append(f"      {idx}. {check}")
        else:
            lines.append(f"      1. {pack.missing_criteria_label}")
    if case.error_message:
        lines.append(f"    {pack.error_label}: {case.error_message}")
    return lines


def render_summary_text(
    suite: ReadableSuite,
    language: str,
    verbose: int = 0,
    include_what: bool = False,
    include_steps: bool = False,
    include_display_name: bool = False,
) -> str:
    """Produce a localized textual summary with configurable case detail levels."""
    counts = suite.counts()
    lines: list[str] = []
    summary_pack = get_language_pack(language)

    lines.append(summary_pack.summary_title)
    lines.append("")
    lines.append(f"- Total: {counts.get('total', 0)}")

    for key in ("passed", "failed", "skipped", "error", "xfailed", "xpassed", "collected"):
        if key in counts:
            lines.append(f"- {_status_label(key, summary_pack.code)}: {counts[key]}")

    if verbose >= 1 or include_what or include_steps or include_display_name:
        lines.append("")
        lines.append(summary_pack.list_title)
        lines.append("")
        for case in suite.cases:
            lines.extend(_render_case_lines(case, summary_pack, include_what, include_steps, include_display_name))

    error_count = counts.get("error", 0)
    xfailed_count = counts.get("xfailed", 0)
    xpassed_count = counts.get("xpassed", 0)
    deselected_count = getattr(suite, "deselected", 0)
    warning_count = getattr(suite, "warnings", 0)

    total_resolved = counts.get("total", 0)
    if total_resolved == 0:
        no_tests_label = _status_label("no_tests", summary_pack.code)
        lines.append("")
        lines.append(no_tests_label)
        return "\n".join(lines).rstrip()

    final_summary = summary_pack.final_summary_template.format(
        total=counts.get("total", 0),
        passed=counts.get("passed", 0),
        failed=counts.get("failed", 0),
        skipped=counts.get("skipped", 0),
    )
    if xfailed_count:
        xfailed_label = _status_label("xfailed", summary_pack.code)
        final_summary += f", {xfailed_label}={xfailed_count}"
    if xpassed_count:
        xpassed_label = _status_label("xpassed", summary_pack.code)
        final_summary += f", {xpassed_label}={xpassed_count}"
    if error_count:
        error_label = _status_label("error", summary_pack.code)
        final_summary += f", {error_label}={error_count}"
    if deselected_count:
        deselected_label = _status_label("deselected", summary_pack.code)
        final_summary += f", {deselected_label}={deselected_count}"
    if warning_count:
        warning_label = _status_label("warnings", summary_pack.code)
        final_summary += f", {warning_label}={warning_count}"
    lines.append("")
    lines.append(final_summary)

    return "\n".join(lines).rstrip()


def render_tree_text(suite: ReadableSuite, include_steps: bool = False) -> str:
    """Render the suite as a hierarchical tree grouped by module and class."""
    grouped: dict[str, dict[str, list]] = {}
    for case in suite.cases:
        by_class = grouped.setdefault(case.module_path, {})
        class_key = case.class_name or "<module>"
        by_class.setdefault(class_key, []).append(case)

    lines: list[str] = []
    for module_name in sorted(grouped):
        lines.append(module_name)
        for class_name in sorted(grouped[module_name]):
            class_cases = grouped[module_name][class_name]
            if class_name != "<module>":
                lines.append(f"  {class_name}")
                base_indent = "    "
            else:
                base_indent = "  "

            for idx, case in enumerate(class_cases, 1):
                lines.append(f"{base_indent}{idx}. {case.display_name}")
                if include_steps and case.steps:
                    for step_idx, step in enumerate(case.steps, 1):
                        lines.append(f"{base_indent}  {idx}.{step_idx} {step}")

    return "\n".join(lines)


def render_markdown(suite: ReadableSuite, language: str) -> str:
    """Generate a markdown document that documents each test in the suite."""
    language_pack = get_language_pack(language)

    lines = [
        f"# {language_pack.markdown_title}",
        f"_{language_pack.markdown_generated_on} {datetime.now().strftime('%Y-%m-%d %H:%M')}_",
        "",
    ]

    by_module: dict[str, list] = {}
    for case in suite.cases:
        by_module.setdefault(case.module_path, []).append(case)

    for module_name in sorted(by_module):
        lines.append(f"## {module_name}")
        lines.append("")
        for idx, case in enumerate(by_module[module_name], 1):
            lines.append(f"### {idx}. {case.display_name}")
            lines.append(f"- nodeid: `{case.nodeid}`")
            lines.append(f"- status: `{case.status}`")
            if case.what:
                lines.append(f"- **{language_pack.markdown_what_label}:** {case.what}")
            if case.steps:
                lines.append(f"- **{language_pack.markdown_steps_label}:**")
                for step_idx, step in enumerate(case.steps, 1):
                    lines.append(f"  {step_idx}. {step}")
            if case.criteria:
                lines.append(f"- **{language_pack.markdown_criteria_label}:**")
                for check_idx, check in enumerate(case.criteria, 1):
                    lines.append(f"  {check_idx}. {check}")
            lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def parse_pytest_output(text: str) -> dict:
    """Extract pytest statistics and per-case status from a raw log dump."""
    import re

    collected = None
    duration = ""
    cases = []
    summary = {}

    collected_match = re.search(r"collected\s+(\d+)\s+items", text)
    if collected_match:
        collected = int(collected_match.group(1))

    case_pattern = re.compile(
        r"^(?P<nodeid>\S+)\s+(?P<status>PASSED|FAILED|SKIPPED|XPASS|XFAIL|ERROR)\b",
        re.MULTILINE,
    )
    for match in case_pattern.finditer(text):
        cases.append(
            {
                "nodeid": match.group("nodeid"),
                "status": match.group("status"),
            }
        )

    summary_match = re.search(r"=+\s*(.*?)\s+in\s+([0-9.]+s)\s*=+", text)
    if summary_match:
        duration = summary_match.group(2)
        for chunk in summary_match.group(1).split(","):
            chunk = chunk.strip()
            count_match = re.match(r"(\d+)\s+([a-zA-Z]+)", chunk)
            if count_match:
                summary[count_match.group(2).lower()] = int(count_match.group(1))

    if cases and not summary:
        for case in cases:
            key = case["status"].lower()
            summary[key] = summary.get(key, 0) + 1

    return {
        "collected": collected,
        "cases": cases,
        "summary": summary,
        "duration": duration,
    }


def render_natural_pytest_summary(report: dict, language: str) -> str:
    """Build a short natural-language summary from parsed pytest metrics."""
    summary = report["summary"]
    collected = report["collected"]
    duration = report["duration"] or "unknown"
    failed_cases = [c["nodeid"] for c in report["cases"] if c["status"] in {"FAILED", "ERROR"}]

    if language == "es":
        lines = ["Resumen natural de pytest"]
        if collected is not None:
            lines.append(f"- Se recolectaron {collected} tests.")
        if summary:
            parts = []
            if "passed" in summary:
                parts.append(f"{summary['passed']} pasaron")
            if "failed" in summary:
                parts.append(f"{summary['failed']} fallaron")
            if "error" in summary:
                parts.append(f"{summary['error']} tuvieron error")
            if "skipped" in summary:
                parts.append(f"{summary['skipped']} fueron omitidos")
            lines.append(f"- Resultado: {', '.join(parts)}.")
        lines.append(f"- Tiempo total: {duration}.")
        if failed_cases:
            lines.append("- Tests con falla/error:")
            lines.extend([f"  - {nodeid}" for nodeid in failed_cases])
        else:
            lines.append("- No se detectaron fallas.")
        return "\n".join(lines)

    lines = ["Pytest natural-language summary"]
    if collected is not None:
        lines.append(f"- Collected {collected} tests.")
    if summary:
        parts = []
        if "passed" in summary:
            parts.append(f"{summary['passed']} passed")
        if "failed" in summary:
            parts.append(f"{summary['failed']} failed")
        if "error" in summary:
            parts.append(f"{summary['error']} had errors")
        if "skipped" in summary:
            parts.append(f"{summary['skipped']} skipped")
        lines.append(f"- Result: {', '.join(parts)}.")
    lines.append(f"- Total time: {duration}.")
    if failed_cases:
        lines.append("- Failed/error tests:")
        lines.extend([f"  - {nodeid}" for nodeid in failed_cases])
    else:
        lines.append("- No failures detected.")
    return "\n".join(lines)
