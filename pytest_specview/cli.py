#!/usr/bin/env python3
"""
specview.py - Interactive spec viewer for pytest
"""

import argparse
import csv
import io
import re
import sys
from datetime import datetime
from pathlib import Path

from pytest_specview.i18n import get_i18n


# --- ANSI colors -----------------------------------------------------------
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
CYAN = "\033[36m"
WHITE = "\033[37m"
RED = "\033[31m"
BLUE = "\033[34m"


def clr(text, *codes):
    return "".join(codes) + str(text) + RESET


def detect_requested_language(argv: list[str]) -> str:
    for i, arg in enumerate(argv):
        if arg == "--lang" and i + 1 < len(argv):
            return argv[i + 1]
        if arg.startswith("--lang="):
            return arg.split("=", 1)[1]
    return "auto"


def build_parser(i18n):
    parser = argparse.ArgumentParser(description=i18n.t("app_description"))
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help=i18n.t("path_help"),
    )
    parser.add_argument(
        "--export",
        choices=["md", "csv"],
        help=i18n.t("export_help"),
    )
    parser.add_argument(
        "--output",
        help=i18n.t("output_help"),
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help=i18n.t("all_help"),
    )
    parser.add_argument(
        "--lang",
        choices=["auto", "en", "es"],
        default="auto",
        help=i18n.t("lang_help"),
    )
    return parser


# --- Parsing ---------------------------------------------------------------

def find_spec_files(root: Path) -> list[Path]:
    """Find all .spec.md files under a directory."""
    return sorted(root.rglob("*.spec.md"))


def parse_spec_file(path: Path, i18n) -> dict:
    """Parse a .spec.md file in English or Spanish into a normalized structure."""
    content = path.read_text(encoding="utf-8")
    lines = content.splitlines()

    result = {
        "file": path,
        "title": "",
        "tests": [],
    }

    current_test = None
    in_steps = False
    what_labels = i18n.accepted_field_labels("what")
    steps_labels = i18n.accepted_field_labels("steps")

    for line in lines:
        stripped = line.strip()

        if stripped.startswith("# ") and not result["title"]:
            result["title"] = stripped[2:].strip()
            continue

        if stripped.startswith("## "):
            if current_test:
                result["tests"].append(current_test)
            current_test = {
                "name": stripped[3:].strip(),
                "what": "",
                "steps": [],
            }
            in_steps = False
            continue

        if current_test is None:
            continue

        matched_label = next((label for label in what_labels if stripped.startswith(label)), None)
        if matched_label is not None:
            current_test["what"] = stripped[len(matched_label):].strip()
            in_steps = False
            continue

        if stripped in steps_labels:
            in_steps = True
            continue

        if in_steps and stripped:
            step_match = re.match(r"^(\d+\.|-)\s+(.*)", stripped)
            if step_match:
                current_test["steps"].append(step_match.group(2).strip())

    if current_test:
        result["tests"].append(current_test)

    return result


# --- Terminal rendering ----------------------------------------------------

def render_spec(spec: dict, i18n, compact: bool = False):
    """Print a complete spec in the terminal with readable formatting."""
    title = spec["title"] or spec["file"].name
    tests = spec["tests"]

    print()
    print(clr(f"{i18n.t('file_label')} {title}", BOLD, CYAN))
    print(clr(f"   {spec['file']}", DIM))
    print(clr("-" * 60, DIM))

    if not tests:
        print(clr(f"  {i18n.t('no_documented_tests')}", DIM, YELLOW))
        return

    for i, test in enumerate(tests, 1):
        marker = clr(f"  [{i}]", BOLD, BLUE)
        name = clr(test["name"], BOLD, WHITE)
        print(f"{marker} {name}")

        if test["what"]:
            print(clr(f"       -> {test['what']}", YELLOW))

        if not compact and test["steps"]:
            for j, step in enumerate(test["steps"], 1):
                print(clr(f"         {j}. {step}", DIM))

        if i < len(tests):
            print()

    print()


def render_summary(specs: list[dict], i18n):
    """Show spec coverage summary."""
    total_tests = sum(len(s["tests"]) for s in specs)
    documented = sum(1 for s in specs for t in s["tests"] if t["what"] or t["steps"])
    undocumented = total_tests - documented

    print(clr(f"\n{i18n.t('summary_title')}", BOLD))
    print(f"  {i18n.t('summary_spec_files'):<16}: {clr(len(specs), BOLD, GREEN)}")
    print(f"  {i18n.t('summary_total_tests'):<16}: {clr(total_tests, BOLD, WHITE)}")
    print(f"  {i18n.t('summary_documented'):<16}: {clr(documented, BOLD, GREEN)}")
    if undocumented:
        print(f"  {i18n.t('summary_missing_details'):<16}: {clr(undocumented, BOLD, YELLOW)}")
    print()


# --- Interactive mode ------------------------------------------------------

def interactive_mode(specs: list[dict], i18n):
    """Interactive menu for browsing specs."""
    if not specs:
        print(clr(f"\n  {i18n.t('no_spec_files')}\n", YELLOW))
        return

    while True:
        print(clr(f"\n{i18n.t('available_specs')}", BOLD))
        for i, spec in enumerate(specs, 1):
            title = spec["title"] or spec["file"].name
            n = len(spec["tests"])
            label = clr(f"  [{i}]", BOLD, BLUE)
            ntests = clr(f"({n} tests)", DIM)
            print(f"{label} {title}  {ntests}")

        print(clr(f"\n  {i18n.t('view_all_quit')}", DIM))
        print()

        choice = input(clr(f"  {i18n.t('choose_number')}", CYAN)).strip().lower()

        if choice == "q":
            break
        if choice == "a":
            for spec in specs:
                render_spec(spec, i18n)
            render_summary(specs, i18n)
            continue

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(specs):
                render_spec(specs[idx], i18n)
                _test_detail_menu(specs[idx], i18n)
            else:
                print(clr(f"  {i18n.t('number_out_of_range')}", RED))
        except ValueError:
            print(clr(f"  {i18n.t('invalid_option')}", RED))


def _test_detail_menu(spec: dict, i18n):
    """Submenu for viewing details of an individual test."""
    tests = spec["tests"]
    if not tests:
        return

    while True:
        print(clr(f"  {i18n.t('detail_menu')}", DIM))
        choice = input(clr(f"  {i18n.t('detail_prompt')}", CYAN)).strip().lower()

        if choice == "b":
            break
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(tests):
                test = tests[idx]
                print()
                print(clr(f"  > {test['name']}", BOLD, WHITE))
                if test["what"]:
                    print(clr(f"    {i18n.field_label('what')}: {test['what']}", YELLOW))
                if test["steps"]:
                    print(clr(f"    {i18n.field_label('steps')}:", BOLD))
                    for j, step in enumerate(test["steps"], 1):
                        print(f"      {clr(j, CYAN)}. {step}")
                else:
                    print(clr(f"    {i18n.t('no_documented_steps')}", DIM))
                print()
            else:
                print(clr(f"  {i18n.t('number_out_of_range')}", RED))
        except ValueError:
            print(clr(f"  {i18n.t('invalid_option')}", RED))


# --- Export ----------------------------------------------------------------

def export_markdown(specs: list[dict], i18n) -> str:
    lines = [
        f"# {i18n.t('test_specs_title')}",
        f"_{i18n.t('generated_on')} {datetime.now().strftime('%Y-%m-%d %H:%M')}_",
        "",
    ]
    for spec in specs:
        title = spec["title"] or spec["file"].name
        lines.append(f"## {title}")
        lines.append(f"`{spec['file']}`")
        lines.append("")
        for i, test in enumerate(spec["tests"], 1):
            lines.append(f"### {i}. {test['name']}")
            if test["what"]:
                lines.append(f"**{i18n.field_label('what')}:** {test['what']}")
                lines.append("")
            if test["steps"]:
                lines.append(f"**{i18n.field_label('steps')}:**")
                for j, step in enumerate(test["steps"], 1):
                    lines.append(f"{j}. {step}")
                lines.append("")
    return "\n".join(lines)


def export_csv(specs: list[dict], i18n) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        i18n.t("file_label"),
        i18n.t("test_label"),
        i18n.field_label("what"),
        i18n.field_label("steps"),
    ])
    for spec in specs:
        title = spec["title"] or spec["file"].name
        for test in spec["tests"]:
            steps = " | ".join(test["steps"]) if test["steps"] else ""
            writer.writerow([title, test["name"], test["what"], steps])
    return output.getvalue()


# --- Main ------------------------------------------------------------------

def main(argv: list[str] | None = None):
    argv = list(sys.argv[1:] if argv is None else argv)
    i18n = get_i18n(detect_requested_language(argv))
    parser = build_parser(i18n)
    args = parser.parse_args(argv)

    root = Path(args.path)

    if not root.exists():
        i18n = get_i18n(args.lang)
        print(clr(f"\n  {i18n.t('error_path_missing', root=root)}\n", RED))
        sys.exit(1)

    spec_files = find_spec_files(root)
    i18n = get_i18n(args.lang, spec_files=spec_files)
    specs = [parse_spec_file(f, i18n) for f in spec_files]

    if args.export:
        if args.export == "md":
            content = export_markdown(specs, i18n)
            ext = "md"
        else:
            content = export_csv(specs, i18n)
            ext = "csv"

        filename = args.output or f"specs_{datetime.now().strftime('%Y%m%d_%H%M')}.{ext}"
        Path(filename).write_text(content, encoding="utf-8")
        print(clr(f"\n  ✓ {i18n.t('exported_to', filename=filename)}\n", GREEN))
        return

    if args.all:
        if not specs:
            print(clr(f"\n  {i18n.t('no_spec_files')}\n", YELLOW))
        for spec in specs:
            render_spec(spec, i18n)
        render_summary(specs, i18n)
        return

    print(clr(f"\n  {i18n.t('app_banner')}", BOLD, CYAN))
    print(clr(f"  {i18n.t('searching_in', root=root.resolve())}", DIM))
    interactive_mode(specs, i18n)


if __name__ == "__main__":
    main()
