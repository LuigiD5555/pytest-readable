# pytest-readable

![Python](https://img.shields.io/badge/python-3.9+-blue)
![pytest plugin](https://img.shields.io/badge/pytest-plugin-green)
![License](https://img.shields.io/badge/license-Apache%202.0-blue)
![Status](https://img.shields.io/badge/status-pre--release-orange)

`pytest-readable` is a pytest plugin that transforms test suites into **readable specifications and structured documentation**.

Instead of treating tests as opaque code, pytest-readable extracts structured metadata from decorated tests and renders it as:

- human-readable CLI summaries
- hierarchical test trees
- Markdown documentation
- structured exports (CSV / JSON)

This helps teams keep **tests, documentation, and specifications aligned**.

---

## Why pytest-readable exists

In many projects, tests contain valuable information about system behavior, but that information is difficult to read or share outside the codebase.

`pytest-readable` bridges that gap by turning test metadata into **readable specifications**.

It enables workflows such as:

- **Living documentation** generated directly from tests
- **Readable summaries** of complex test suites
- **Exportable specifications** for documentation or reporting
- **Clear test intent** for onboarding and collaboration

The goal is simple:

**make tests understandable without reading the implementation.**

---

# Example

## Test

```python
from pytest_readable import readable


@readable(
    title="User login succeeds with valid credentials",
    description="A registered user can log in using correct email and password.",
    steps=[
        "User submits login form",
        "Authentication service validates credentials",
        "Session token is issued"
    ],
    criteria=[
        "Login request returns HTTP 200",
        "Session token is present",
        "User is redirected to dashboard"
    ]
)
def test_login_success():
    ...
```

## CLI output

```
Authentication
 └─ User login succeeds with valid credentials
    ✓ Login request returns HTTP 200
    ✓ Session token is present
    ✓ User is redirected to dashboard
```

## Markdown export

```
### User login succeeds with valid credentials

A registered user can log in using correct email and password.

Steps
- User submits login form
- Authentication service validates credentials
- Session token is issued

Acceptance Criteria
- Login request returns HTTP 200
- Session token is present
- User is redirected to dashboard
```

---

# Requirements

- Python **3.9+**
- pytest **7+**

---

# Installation

Install from PyPI:

```bash
pip install pytest-readable
```

Install locally for development:

```bash
pip install -e .
```

---

# Quick start

Run your test suite normally:

```bash
pytest
```

Enable readable summaries:

```bash
pytest --readable
```

Export documentation (Markdown):

```bash
pytest --readable --export=markdown
```

The `--export` flag is a shortcut for `--readable-docs --readable-format=FORMAT`, so you can also run `pytest --readable --export=csv` or add `--readable-out=docs/tests-readable.md` to set a different path.

---

# CLI helper

pytest-readable also provides a small CLI helper for convenience.

Instead of remembering plugin flags, you can invoke pytest-readable using the `readable` command:

```bash
readable pytest
```

Example:

```bash
readable pytest tests/
```

This is equivalent to running:

```bash
pytest --readable
```

To export Markdown documentation for a specific run you can append the new `--export` flag:

```bash
readable pytest tests/ --export=markdown
```

That expands to `pytest --readable --export=markdown` under the hood.

The CLI wrapper exists mainly as a **mnemonic shortcut**, making it easier to remember and invoke readable test summaries.

You can inspect available CLI options with:

```bash
readable --help
```

To quickly audit missing metadata and speed up migrations:

```bash
readable --find-missing
```

Optional custom test root:

```bash
readable --find-missing --tests-root=tests
```

---

# Using the `@readable` decorator

Add the decorator to tests to describe behavior and expected results.

```python
from pytest_readable import readable


@readable(
    title="Search returns matching results",
    steps=[
        "User enters search query",
        "System queries the search index",
        "Results are returned"
    ],
    criteria=[
        "Response status is 200",
        "Results contain matching items"
    ]
)
def test_search():
    ...
```

pytest-readable extracts this metadata and uses it to generate summaries and documentation.

---

# Features

- **Readable test summaries**
- **Hierarchical test tree view**
- **Decorator-based metadata**
- **Markdown documentation export**
- **CSV / JSON structured exports**
- **CLI helper command (`readable`)**
- **Multiple language support**
- **pytest-native plugin architecture**

pytest-readable works directly with pytest’s collection system, so it integrates naturally with existing test suites.

---

# Language support

pytest-readable supports configurable output language.

Currently supported:

- English
- Spanish

Example:

```bash
pytest --readable-lang=es
```

The architecture allows additional languages to be added easily.

---

# Use cases

pytest-readable is useful when:

- a test suite doubles as **behavior documentation**
- teams want **clear test intent**
- tests should be understandable by **non-developers**
- specifications need to be **exported for reports**
- projects want **living documentation derived from tests**

Typical environments include:

- QA and validation pipelines
- test-driven development (TDD) workflows
- documentation-driven projects
- internal platform teams

---

# Development

Clone the repository:

```bash
git clone https://github.com/your-org/pytest-readable
cd pytest-readable
```

Install in development mode:

```bash
pip install -e .
```

Run tests:

```bash
pytest -q
```

---

# Roadmap

Planned improvements include:

- additional output formats
- richer documentation exports
- expanded language support
- deeper TDD-oriented tooling
- improved structured metadata for reporting pipelines

---

# Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to contribute.

---

# Changelog

See [CHANGELOG.md](CHANGELOG.md) for release history.

---

# License

Apache License 2.0

See the [LICENSE](LICENSE) file for details.
