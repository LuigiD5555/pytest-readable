# pytest-readable  
  
Turn pytest tests into readable specifications and documentation.  
  
`pytest-readable` is a lightweight pytest plugin that converts collected tests into human-readable summaries and structured documentation.  
  
Instead of treating tests only as code, the plugin allows tests to behave like **executable specifications** by attaching human-friendly metadata using decorators.  
  
The plugin can generate:  
  
- readable CLI summaries  
- hierarchical test trees  
- Markdown documentation  
- CSV exports  
  
This helps keep **tests, documentation, and specifications aligned**, making test suites easier to understand for developers, teams, and AI-assisted tooling.  
  
---  

## Compatibility

- Python 3.10+
- pytest 9.x

## Installation  
  
```bash  
pip install pytest-readable

For local development:

``` Bash
pip install -e .
```

## Quick Start

```bash
pytest --readable
```

Primary tree view:

```bash
pytest --collect-only --readable-tree
```

## Main Options

- `--readable`: readable summary integrated in pytest output
- `--readable-tree`: hierarchical test tree
- `--readable-docs`: export readable docs
- `--readable-out=PATH`: output path for exported docs
- `--readable-format=markdown|csv`: export format
- `--readable-lang=auto|es|en`: output language
- `--readable-include-steps`: include documented steps in output

`--readable-lang=auto` tries to infer language from `@readable(...)` metadata first,
then falls back to environment (`PYTEST_READABLE_LANG`, `LC_ALL`, `LANG`).
`criteria` (and `criteria_en` / `criteria_es`) defines pass conditions shown after
the step breakdown in detailed output.

Example export:

```bash
pytest --readable-docs --readable-format=markdown --readable-out=docs/tests-readable.md --collect-only
pytest --readable-docs --readable-format=csv --readable-out=docs/tests-readable.csv --collect-only
```

## Human Metadata

Decorator-first metadata:

```python
from pytest_readable.decorators import readable

@readable(
    title_en="Pipeline query works",
    title_es="Pipeline de consulta funciona",
    intent_en="Validates embedding, retrieval and blackboard flow",
    intent_es="Valida el flujo de embedding, retrieval y blackboard",
    steps_en=["Build input", "Run pipeline", "Assert outputs"],
    steps_es=["Construir input", "Ejecutar pipeline", "Validar salidas"],
    criteria_en=["Returns expected document count", "No runtime errors"],
    criteria_es=["Retorna el numero esperado de documentos", "No hay errores de ejecucion"],
)
def test_query_pipeline():
    ...
```

Single-language shorthand (same API you asked for):

```python
from pytest_readable.decorators import readable

@readable(
    title="test_sample.py",
    intent="Parses english fields",
    steps="""
1. Read the file
2. Extract the fields
""",
    criteria=[
        "Returns parsed english fields",
        "Does not raise exceptions",
    ],
)
def test_parse_spec_file_accepts_english_labels(tmp_path):
    ...
```

All readable documentation now lives in decorators (`@readable(...)`) inside test files.
No `.spec.md` files are used or generated.

## Optional Helper CLI

`readable` is kept as secondary wrapper:

```bash
readable -q
```

## Project Layout

```text
src/
  pytest_readable/
    __init__.py
    plugin.py
    cli.py
    core/
      models.py
      parser.py
      renderer.py
      exporters.py
      services.py
```

## Limitations

- Tree hierarchy is based on pytest collection (`module -> class -> test`) and decorator metadata from `@readable(...)`.

## Language-focused tests

- Some plugin tests are gated behind language flags to keep the main run clean: `--readable-lang=en`, `--readable-lang=es`, and `--readable-lang=auto`.  
- They are implemented via markers in `tests/conftest.py` (`en_lang_only`, `es_lang_only`, `auto_lang_only`), so changes to those tests should be done with those modes in mind.
