# pytest-readable

Native pytest plugin that turns collected tests into a readable summary/tree and exports docs.

## Installation

```bash
pip install pytest-readable
```

For local development:

```bash
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

Example export:

```bash
pytest --readable-docs --readable-format=markdown --readable-out=docs/tests-readable.md --collect-only
pytest --readable-docs --readable-format=csv --readable-out=docs/tests-readable.csv --collect-only
```

## Human Metadata

Decorator-first metadata:

```python
from pytest_readable.decorators import spec

@spec(
    title_en="Pipeline query works",
    title_es="Pipeline de consulta funciona",
    what_en="Validates embedding, retrieval and blackboard flow",
    what_es="Valida el flujo de embedding, retrieval y blackboard",
    steps_en=["Build input", "Run pipeline", "Assert outputs"],
    steps_es=["Construir input", "Ejecutar pipeline", "Validar salidas"],
)
def test_query_pipeline():
    ...
```

Optional markdown fallback next to the test file:

```markdown
# test_query_pipeline.py

## Pipeline de consulta
**Qué prueba:** Que el pipeline completo produce resultados coherentes.
**Pasos:**
1. Embedding
2. Retrieval
3. Blackboard
```

## Optional Helper CLI

`readable` is kept as secondary wrapper:

```bash
readable -q
readable --generate-spec-md tests/
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

- Tree hierarchy is based on pytest collection (`module -> class -> test`), enriched by decorator or `.spec.md` metadata.
- `.spec.md` fallback matching is best-effort when names differ from pytest node ids.
