# pytest-specview

Interactive test documentation viewer for pytest projects. It reads `.spec.md` files — natural-language documentation stored alongside each test file — and presents them in the terminal with navigation, coverage summaries, and export support.

---

## What problem it solves

Pytest tests often have technical names (`test_embed_handles_empty_string`) and code that needs extra context to understand. `pytest-specview` adds a parallel documentation layer: `.spec.md` files that explain in human language what each test verifies, without touching the code.

```
tests/
├── test_embedder.py          ← test code
└── test_embedder.spec.md     ← readable documentation
```

---

## Installation

### From PyPI (once published)

```bash
pip install pytest-specview
```

### From the repository (local development install)

```bash
git clone <repo-url>
cd pytest-specview
pip install -e .
```

The `-e` option installs in editable mode, so any source code change is reflected without reinstalling.

---

## Usage

### Interactive mode (default)

```bash
specview                  # search for .spec.md from the current directory
specview tests/           # search in a specific folder
```

It shows a numbered menu with every spec file found. You can navigate to a specific file and then to an individual test.

```
== AVAILABLE SPECS ==========================
  [1] test_embedder.py  (3 tests)
  [2] test_pipeline.py  (2 tests)

  [a] View all  [q] Quit

  Choose a number: _
```

---

## `.spec.md` file format

Each test file has a matching `.spec.md` file in the same directory:

```markdown
# test_file_name.py

## Test name in natural language
**What it tests:** A single sentence describing the verified behavior.
**Steps:**
1. First step in human language
2. Second step
3. What is verified at the end
```

Spanish labels are also valid:

```markdown
# test_file_name.py

## Nombre del test en lenguaje natural
**Qué prueba:** Una sola oración describiendo el comportamiento verificado.
**Pasos:**
1. Primer paso en lenguaje humano
2. Segundo paso
3. Qué se verifica al final
```

---

## Package structure

```
pytest-specview/
├── pyproject.toml              ← package metadata and CLI entry point
├── README.md
└── pytest_specview/
    ├── __init__.py             ← package version
    └── cli.py                  ← all logic (parsing, rendering, export)
```

---

## Full options

```
specview [path] [--export {md,csv}] [--output FILE] [--all]

Arguments:
  path                  Directory where .spec.md files are searched (default: .)

Options:
  --all                 Show all specs without the interactive menu
  --export {md,csv}     Export to Markdown or CSV
  --output FILE         Output file name for --export
  -h, --help            Show this help message
```
