"""Secondary CLI helper for pytest-readable features."""

import argparse
import subprocess
import sys
from pathlib import Path

from pytest_readable.core.parser import generate_spec_markdown_from_decorators
from pytest_readable.i18n import get_i18n


def build_parser() -> argparse.ArgumentParser:
    """Return the argparse parser that recognizes helper options."""
    parser = argparse.ArgumentParser(description="Helper CLI for pytest-readable")
    parser.add_argument("pytest_args", nargs="*", help="Arguments forwarded to pytest")
    parser.add_argument(
        "--lang",
        choices=["auto", "en", "es"],
        default="auto",
        help="Language used by --generate-spec-md",
    )
    parser.add_argument(
        "--generate-spec-md",
        metavar="PATH",
        help="Generate .spec.md files from @spec decorators under PATH",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Entrypoint invoked by the `readable` script; forwards to pytest."""
    args = build_parser().parse_args(argv)

    if args.generate_spec_md:
        root = Path(args.generate_spec_md)
        i18n = get_i18n(args.lang)
        generated = generate_spec_markdown_from_decorators(root, i18n)
        print(f"generated {len(generated)} .spec.md files")
        return 0

    pytest_args = list(args.pytest_args)
    if not any(part.startswith("--readable") for part in pytest_args):
        pytest_args.insert(0, "--readable")

    command = ["pytest", *pytest_args]
    return subprocess.call(command)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
