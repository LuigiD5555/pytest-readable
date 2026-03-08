# pytest-translator

Interactive test documentation viewer for pytest projects. It reads natural-language metadata from `@spec(...)` decorators (preferred source), falls back to `.spec.md` files when needed, and presents everything in the terminal with navigation, coverage summaries, and export support.

Specs can be written in English or Spanish. The parser accepts both `What it tests`/`Steps` and `Qué prueba`/`Pasos`, and the CLI/export language can be selected with `--lang en|es` or auto-detected from the spec content first, then from the environment (`SPECVIEW_LANG`, `LC_ALL`, or `LANG`).

---

## What problem it solves

Pytest tests often have technical names (`test_embed_handles_empty_string`) and code that needs extra context to understand. `pytest-translator` adds a parallel documentation layer driven by decorators in the test code, with optional generated `.spec.md` artifacts.

```
tests/
├── test_embedder.py          <- test code
└── test_embedder.spec.md     <- optional generated readable documentation
```

---

## Installation

### From PyPI (once published)

```bash
pip install pytest-translator
```

### From the repository (local development install)

```bash
git clone <repo-url>
cd pytest-translator
pip install -e .
```

The `-e` option installs in editable mode, so any source code change is reflected without reinstalling.

### Verify the installation

```bash
specview --help
specview-compile-locales
```

Requirements: Python 3.10 or newer. No external dependencies - stdlib only.

For tests, prefer `python3 -m pytest` to ensure the same interpreter used by pip install is used for test execution.

---

## Usage

### Interactive mode (default)

```bash
specview                  # search for .spec.md from the current directory
specview tests/           # search in a specific folder
specview --lang es tests/ # render the UI and exports in Spanish
SPECVIEW_LANG=es specview # use environment-driven Spanish output
```

It shows a numbered menu with every spec file found. You can navigate to a specific file and then to an individual test.

```
== AVAILABLE SPECS ==========================
  [1] test_embedder.py  (3 tests)
  [2] test_pipeline.py  (2 tests)

  [a] View all  [q] Quit

  Choose a number: _
```

### Show everything at once

```bash
specview --all tests/
```

It prints every spec in sequence and finishes with a coverage summary:

```
== SUMMARY ==================================
  Spec files      : 2
  Total tests     : 5
  Documented      : 5
```

### Decorator-first workflow (recommended)

```python
from pytest_translator.decorators import spec

@spec(
    title_en="Handles empty payload",
    title_es="Maneja carga vacia",
    what_en="Returns a controlled validation error",
    what_es="Devuelve un error de validacion controlado",
    steps_en=["Send empty payload", "Assert ValueError"],
    steps_es=["Enviar carga vacia", "Validar ValueError"],
)
def test_empty_payload():
    ...
```

You can generate `.spec.md` files from decorators when you need shareable docs:

```bash
specview --generate-spec-md tests/
```

### Export

```bash
specview --export md tests/              # generates specs_YYYYMMDD_HHMM.md
specview --export csv tests/             # generates specs_YYYYMMDD_HHMM.csv
specview --export md --output docs/specs.md tests/   # custom name
```

The exported Markdown groups all specs into a single navigable file. The CSV includes the columns `File`, `Test`, `What it tests`, and `Steps`, which is useful for importing into Notion, Jira, or spreadsheets.

When `--lang es` is used, export headings and CSV headers are also generated in Spanish.

If `--lang auto` is used, `specview` first looks at the spec labels it finds (`What it tests`/`Steps` vs `Qué prueba`/`Pasos`) and then falls back to your environment if the content is mixed or ambiguous.

## Locale maintenance

If you edit the gettext catalogs in `pytest-translator/locale/*/LC_MESSAGES/*.po`, recompile the binary `.mo` files with:

```bash
specview-compile-locales
```

That command regenerates every `.mo` file from the checked-in `.po` sources, so runtime translations stay in sync with your edits.

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

### Real example

```markdown
# test_query_pipeline.py

## Retrieves the top-k most relevant documents for a query
**What it tests:** The retriever returns exactly k documents ordered by score
**Steps:**
1. Insert 10 test documents into Weaviate
2. Run a query with k=3
3. Verify that exactly 3 results are returned
4. Verify they are ordered from highest to lowest relevance
5. Clean up the test documents at the end
```

### Naming rules

| Test file                      | Spec file                           |
|--------------------------------|-------------------------------------|
| `tests/test_query.py`          | `tests/test_query.spec.md`          |
| `tests/unit/test_embedder.py`  | `tests/unit/test_embedder.spec.md`  |
| `src/test_pipeline.py`         | `src/test_pipeline.spec.md`         |

---

## Package structure

```
pytest-translator/
├── pyproject.toml              <- package metadata and CLI entry point
├── README.md
└── pytest-translator/
    ├── __init__.py             <- package version
    ├── locale/                <- gettext catalogs (.po/.mo) for en/es
    └── cli.py                  <- all logic (parsing, rendering, export)
```

### Internal modules in `cli.py`

| Function | What it does |
|---|---|
| `find_spec_files(root)` | Recursively searches for all `*.spec.md` files under a directory |
| `parse_spec_file(path)` | Parses a `.spec.md` and returns a dict with `title` and `tests[]` |
| `render_spec(spec)` | Prints a spec in the terminal with ANSI colors |
| `render_summary(specs)` | Shows the total count of tests and documented entries |
| `interactive_mode(specs)` | Main navigation menu |
| `_test_detail_menu(spec)` | Submenu for an individual test |
| `export_markdown(specs)` | Serializes all specs to Markdown |
| `export_csv(specs)` | Serializes all specs to CSV |
| `main()` | Entry point: parses args and dispatches the right mode |

The `.spec.md` parser works line by line with three patterns:
- `# text` -> file title (H1, only the first one)
- `## text` -> new test block (H2)
- `**What it tests:**` / `**Qué prueba:**` and `**Steps:**` / `**Pasos:**` -> fields inside each block

---

## Integration with Claude Code (pytest-spec skill)

The repository includes a skill for Claude Code that automatically generates the `.spec.md` whenever a test is written or modified:

```
.claude/skills/pytest-spec/SKILL.md
```

With the skill enabled, when you ask Claude Code to write or modify tests, it generates the spec in the same step and reports:

```
✓ Test written to tests/test_embedder.py
✓ Spec updated at tests/test_embedder.spec.md
```

To enable it, the project's `CLAUDE.md` should include:

```markdown
## Skills
- .claude/skills/pytest-spec/SKILL.md - Generates readable specs alongside each pytest test
```

---

## Full options

```
specview [path] [--export {md,csv}] [--output FILE] [--all] [--lang {auto,en,es}] [--generate-spec-md]

Arguments:
  path                  Directory where .spec.md files are searched (default: .)

Options:
  --all                 Show all specs without the interactive menu
  --export {md,csv}     Export to Markdown or CSV
  --output FILE         Output file name for --export
  --lang {auto,en,es}   Output language for UI and exports
  --generate-spec-md    Generate .spec.md files from @spec decorators
  -h, --help            Show this help message
```
