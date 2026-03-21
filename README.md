# pytest-readable

![PyPI](https://img.shields.io/pypi/v/pytest-readable)
![Python](https://img.shields.io/pypi/pyversions/pytest-readable)
![License](https://img.shields.io/badge/license-MIT-blue)

`pytest-readable` is a pytest plugin that turns tests into human-readable specifications and exports them to Markdown or CSV.

It is useful when you want pytest output to be easier to review, easier to share with non-developers, and easier to reuse as lightweight test documentation.

## The problem it solves

When AI generates your test suite, you end up with 200 tests that pass and no practical way to know if they're testing the right things without reading each one individually.

`pytest-readable` forces explicit intent at the point of writing. Just add a decorator no extra calls, no configuration, no framework to learn and it surfaces intent, steps, and pass conditions in one readable summary so you can audit at a glance instead of diving into code.

## Installation

```bash
pip install pytest-readable
```

## Requirements

- Python 3.10+
- pytest 9.x

## Quick Example

Test:

```python
from pytest_readable import readable


@readable(
    intention="User login succeeds with valid credentials",
    steps=[
        "Create a user",
        "Attempt login with the correct password",
    ],
    criteria=[
        "Login succeeds",
        "A session token is returned",
    ],
)
def test_user_login():
    ...
```

Run:

```bash
pytest --readable-detailed
```

Output:

```text
Readable summary

- Total: 1
- collected: 1

Detailed list

- [unknown] tests/test_auth.py::test_user_login
    What it tests: User login succeeds with valid credentials
    Steps:
      1. Create a user
      2. Attempt login with the correct password
    Pass conditions:
      1. Login succeeds
      2. A session token is returned

Final summary: total=1, passed=0, failed=0, skipped=0
```

## Common Commands

Readable terminal summary:

```bash
pytest --readable
```

This prints a summarized readable report without pytest's native header or footer noise.

Readable detailed report:

```bash
pytest --readable-detailed
```

Detailed aliases:

```bash
pytest --readable --detailed
pytest --readable -d
```

Readable verbose report:

```bash
pytest --readable-verbose
```

Verbose aliases:

```bash
pytest --readable --verbose
pytest --readable -v
```

Export Markdown documentation:

```bash
pytest --readable --export=markdown
```

Export CSV documentation:

```bash
pytest --readable --export=csv
```

Set a custom output path:

```bash
pytest --readable --export=markdown --readable-out=docs/tests-readable.md
```

## When to use pytest-readable

Use `pytest-readable` when you want to:

- make pytest output easier to read
- export test documentation to Markdown or CSV
- review test intent without reading raw test code
- share tests with QA, analysts, or non-developers
- keep tests and lightweight documentation aligned
- present test coverage in a more human-friendly format

## Who it is for

`pytest-readable` is especially useful for:

- solo developers
- small teams
- internal tools
- lightweight QA workflows
- multilingual teams that want readable test output
- projects where tests also serve as living documentation

## Why use it instead of plain pytest output?

Plain pytest output is optimized for test execution and debugging.

`pytest-readable` is optimized for:

- readable review
- explicit test intent
- lightweight documentation export
- sharing tests with people who do not want to read raw test code

## Design Philosophy

`pytest-readable` is intentionally non-inferential.

The plugin does not attempt to interpret test code, infer behavior, or generate missing semantics. It renders only the metadata that the author explicitly declares.

This keeps the plugin:

- deterministic
- framework-agnostic
- compatible with both human-written and AI-generated tests

`pytest-readable` does not try to make tests better. It makes explicitly described tests more readable.

## Scope

This project focuses on:

- readable test intention
- explicit steps
- explicit pass conditions
- pytest-aware rendering
- Markdown and CSV export

It does not aim to become:

- a TDD framework
- a test generator
- an AI interpreter
- a writable test authoring tool

## CLI Helper

The package also installs a small `readable` helper command that forwards to pytest with readable defaults:

```bash
readable pytest tests/
```

Equivalent pytest invocation:

```bash
pytest --readable --color=yes tests/
```

Detailed readable output:

```bash
readable --detailed pytest tests/
readable pytest --detailed tests/
readable pytest -d tests/
```

Verbose readable output:

```bash
readable pytest -v tests/
readable pytest --verbose tests/
```

Mode equivalences:

```bash
readable pytest               -> pytest --readable
readable pytest -d           -> pytest --readable -d
readable pytest --detailed   -> pytest --readable --detailed
readable pytest -v           -> pytest --readable -v
readable pytest --verbose    -> pytest --readable --verbose
```

Note: `-d` works as a readable shorthand when used together with `--readable`, even though `pytest --help` lists the long-form detailed options.

Helper-specific commands:

```bash
readable --help
readable --find-missing
readable --find-missing --tests-root=tests
```

## Decorator Metadata

Document tests with explicit metadata:

```python
from pytest_readable import readable


@readable(
    intention="Search returns matching results",
    steps=[
        "User enters a search query",
        "The system queries the search index",
    ],
    criteria=[
        "The response status is 200",
        "The results contain matching items",
    ],
)
def test_search():
    ...
```

The preferred metadata shape is:

```python
@readable(
    intention="What the test validates",
    steps=["Action performed"],
    criteria=["Expected observable outcome"],
)
```

## Language Support

Supported output languages:

- English
- Spanish

Example:

```bash
pytest --readable-lang=es
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for release history.

## License

MIT License. See [LICENSE](LICENSE) for details.
