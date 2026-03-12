# pytest-readable

![PyPI](https://img.shields.io/pypi/v/pytest-readable)
![Python](https://img.shields.io/pypi/pyversions/pytest-readable)
![License](https://img.shields.io/badge/license-MIT-blue)

`pytest-readable` is a pytest plugin that renders collected tests as human-readable specifications and Markdown or CSV documentation.

It makes explicitly described tests easier to read in the terminal and easier to export as documentation.

## Installation

```bash
pip install pytest-readable
```

## Example

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
pytest --readable --readable-include-steps
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

## Quick Start

Readable terminal summary:

```bash
pytest --readable
```

Readable terminal summary with steps:

```bash
pytest --readable --readable-include-steps
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
pytest --readable -q --no-header --color=yes --readable-include-steps tests/
```

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

## Next Steps

The current release focuses on explicit, detailed readable output.

Next improvements are likely to focus on additional rendering modes:

- a more verbose mode with pytest command context, exit code, and richer execution summaries
- a compact mode that renders only test intentions, without steps or pass conditions

## Development

```bash
git clone https://github.com/LuigiD5555/pytest-readable
cd pytest-readable
pip install -e .
pytest -q
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for release history.

## License

MIT License. See [LICENSE](LICENSE) for details.
