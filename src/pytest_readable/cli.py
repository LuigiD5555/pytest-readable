# Copyright 2026 José Luis López López Prieto and contributors
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

"""Secondary CLI helper for pytest-readable features."""

import argparse
import re
import subprocess
import sys

from pytest_readable.language_registry import supported_languages


ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def _strip_ansi(text: str) -> str:
    """Return `text` without ANSI escape sequences so pytest sections parse cleanly."""
    return ANSI_RE.sub("", text)


def _extract_report_section(text: str, title: str) -> str:
    """Return the block starting at `title` from pytest output, trimmed of summary footers."""
    pattern = rf"(?ms)^=+\s*{re.escape(title)}\s*=+\n.*?(?=^=+\s*.+?\s*=+\n|\Z)"
    match = re.search(pattern, text)
    if not match:
        return ""
    lines = match.group(0).strip().splitlines()
    while lines and re.match(r"^\d+\s+.+\s+in\s+[0-9.]+s$", _strip_ansi(lines[-1]).strip()):
        lines.pop()
    return ("\n".join(lines).strip() + "\n") if lines else ""



def _print_wrapped_output(stdout_text: str, stderr_text: str, returncode: int) -> None:
    """Dump the most relevant pytest summaries to stdout/stderr while honoring returncode."""
    chunks: list[str] = []
    if returncode != 0:
        for title in ("FAILURES", "warnings summary", "short test summary info"):
            section = _extract_report_section(stdout_text, title)
            if section:
                chunks.append(section)

    if chunks:
        print("\n".join(chunk.strip() for chunk in chunks if chunk.strip()))
    elif stdout_text.strip():
        print(stdout_text.strip())

    if stderr_text.strip():
        print(stderr_text.strip(), file=sys.stderr)


def build_parser() -> argparse.ArgumentParser:
    """Return the argparse parser that recognizes helper options."""
    parser = argparse.ArgumentParser(description="Helper CLI for pytest-readable")
    parser.add_argument("pytest_args", nargs="*", help="Arguments forwarded to pytest")
    parser.add_argument(
        "--lang",
        choices=["auto", *supported_languages()],
        default="auto",
        help="Language used by readable output",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Entrypoint invoked by the `readable` script; forwards to pytest."""
    args, passthrough = build_parser().parse_known_args(argv)

    pytest_args = [*args.pytest_args, *passthrough]
    while pytest_args and pytest_args[0] in {"pytest", "py.test"}:
        pytest_args.pop(0)

    if not any(part.startswith("--readable") for part in pytest_args):
        pytest_args.insert(0, "--readable")

    if not any(part.startswith("--readable-lang") for part in pytest_args) and args.lang != "auto":
        pytest_args.append(f"--readable-lang={args.lang}")

    if not any(part.startswith("-q") or part in {"--quiet", "-v", "--verbose"} for part in pytest_args):
        pytest_args.extend(["-q", "--no-header"])

    if not any(part.startswith("--color=") for part in pytest_args):
        pytest_args.append("--color=yes")

    if "--readable-include-steps" not in pytest_args:
        pytest_args.append("--readable-include-steps")

    command = ["pytest", *pytest_args]
    result = subprocess.run(command, text=True, capture_output=True, check=False)
    _print_wrapped_output(result.stdout, result.stderr, result.returncode)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
