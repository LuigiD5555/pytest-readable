# pytest-translator

Interactive natural-language spec viewer for pytest projects. It reads structured metadata from `@spec(...)` decorators first, falls back to `.spec.md` documents generated next to each test file, and renders everything in the terminal with navigation, coverage summaries, and export support.

Specs can be written in English or Spanish. The parser recognizes both `What it tests`/`Steps` and `Qué prueba`/`Pasos`, and the CLI/export language can be set with `--lang en|es` or auto-detected from the spec content first, then from the environment (`PYTEST_TRANSLATOR_LANG`, `LC_ALL`, or `LANG`).

---

## What problem it solves

Pytest tests usually carry technical identifiers like `test_embed_handles_empty_string` and only make sense when you read the code. `pytest-translator` layers a human-readable narrative on top of those tests by letting you document behavior with decorators or `.spec.md` artifacts. Files look like this:

```
tests/
├── test_embedder.py          <- test code
└── test_embedder.spec.md     <- optional generated readable documentation
```

---

## Quick start

1. **Install the tool.**
   ```bash
   python3 -m pip install -e .
   ```
   This registers the `pytest-translator` CLI (and `pytest-translator-compile-locales`) inside your active `test_translator` environment.

2. **Describe tests in human-readable language.** Prefer the decorator-first workflow: import the helper, add language-specific labels, and keep tests readable without touching assertions.
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
   If you need shareable documents, `pytest-translator --generate-spec-md tests/` materializes `.spec.md` files from decorators.

3. **Explore specs through the CLI.**
   ```bash
   pytest-translator tests/
   ```
   The interactive menu lists spec sources, shows coverage, and lets you inspect any test. Add `--lang es` to force Spanish output or rely on auto-detection.

---

## CLI usage

### Interactive mode (default)

```bash
pytest-translator [path]
```

Runs the interactive browser with numbered menus, coverage summaries, and a detail submenu per test. Omit `path` to search the current directory. While viewing, press `a` to render all specs, `q` to quit, or a number to open a single file.

### Show everything at once

```bash
pytest-translator --all tests/
```

Prints every spec sequentially followed by the coverage summary, which is handy for logging or CI checks.

### Export docs to Markdown or CSV

```bash
pytest-translator --export md tests/
pytest-translator --export csv --output docs/specs.csv tests/
```

Exports combine every spec with localized headings. Use `--lang es` to render Spanish labels and column headers.

### Generate `.spec.md` files from decorators

```bash
pytest-translator --generate-spec-md tests/
```

Iterates over `test_*.py` and `*_test.py` files that declare `@spec(...)`, writes Markdown files next to them, and reports how many were created.

### Render a natural-language pytest summary

```bash
pytest-translator --pytest-report pytest.log
cat pytest.log | pytest-translator --pytest-report -
```

Parses raw pytest output, counts statuses, lists failed nodeids, and emits a short summary in English or Spanish depending on `--lang` or `PYTEST_TRANSLATOR_LANG`.

---

## `.spec.md` file format

Each test file can live next to a `.spec.md` twin that describes every test in human language:

```markdown
# test_file_name.py

## Test name in natural language
**What it tests:** A single sentence describing the verified behavior.
**Steps:**
1. First step in human language
2. Second step
3. What is verified at the end
```

Spanish labels are also accepted:

```markdown
# test_file_name.py

## Nombre del test en lenguaje natural
**Qué prueba:** Una sola oración describiendo el comportamiento verificado.
**Pasos:**
1. Primer paso en lenguaje humano
2. Segundo paso
3. Qué se verifica al final
```

Naming rules keep specs aligned with their test modules:

| Test file                      | Spec file                           |
|--------------------------------|-------------------------------------|
| `tests/test_query.py`          | `tests/test_query.spec.md`          |
| `tests/unit/test_embedder.py`  | `tests/unit/test_embedder.spec.md`  |
| `src/test_pipeline.py`         | `src/test_pipeline.spec.md`         |

---

## Locale maintenance

If you edit the gettext catalogs under `pytest_translator/locale/*/LC_MESSAGES/`, recompile them with the helper that ships in `pathlib` style:

```bash
pytest-translator-compile-locales
```

This command rewrites every `.mo` from the checked-in `.po` files, keeping translations synchronized.

If you prefer environment-driven language selection, set `PYTEST_TRANSLATOR_LANG` to `en` or `es`. It takes precedence over `LC_ALL` and `LANG`.

---

## Full options

```
pytest-translator [path] [--export {md,csv}] [--output FILE] [--all] [--lang {auto,en,es}] [--generate-spec-md] [--pytest-report FILE]
```

Arguments:
- `path` &nbsp;&nbsp;&nbsp;&nbsp; Directory where specs are searched (default: `.`)

Options:
- `--export {md,csv}` &nbsp;&nbsp; Export to Markdown or CSV
- `--output FILE` &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Output file name for `--export`
- `--all` &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Print every spec immediately
- `--lang {auto,en,es}` &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Output language for UI and exports
- `--generate-spec-md` &nbsp;&nbsp; Generate `.spec.md` files from decorated tests
- `--pytest-report FILE` &nbsp;&nbsp; Render a natural-language summary from raw pytest output (`-` reads stdin)
- `-h, --help` &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Show this help message
```
