from gettext import GNUTranslations
from pathlib import Path

from pytest_translator.cli import (
    export_csv,
    export_markdown,
    generate_spec_markdown_from_decorators,
    load_specs,
    parse_decorated_spec_file,
    parse_pytest_output,
    parse_spec_file,
    render_natural_pytest_summary,
)
from pytest_translator.compile_locales import compile_po_file
from pytest_translator.i18n import detect_language_from_text, get_i18n, resolve_language


def test_parse_spec_file_accepts_english_labels(tmp_path):
    content = """# test_sample.py

## Handles english labels
**What it tests:** Parses english fields
**Steps:**
1. Read the file
2. Extract the fields
"""
    path = tmp_path / "test_sample.spec.md"
    path.write_text(content, encoding="utf-8")

    spec = parse_spec_file(path, get_i18n("en"))

    assert spec["title"] == "test_sample.py"
    assert spec["tests"][0]["what"] == "Parses english fields"
    assert spec["tests"][0]["steps"] == ["Read the file", "Extract the fields"]


def test_parse_spec_file_accepts_spanish_labels(tmp_path):
    content = """# test_sample.py

## Acepta etiquetas en espanol
**Qué prueba:** Parsea campos en espanol
**Pasos:**
1. Lee el archivo
2. Extrae los campos
"""
    path = tmp_path / "test_sample.spec.md"
    path.write_text(content, encoding="utf-8")

    spec = parse_spec_file(path, get_i18n("es"))

    assert spec["title"] == "test_sample.py"
    assert spec["tests"][0]["what"] == "Parsea campos en espanol"
    assert spec["tests"][0]["steps"] == ["Lee el archivo", "Extrae los campos"]


def test_markdown_export_localizes_title_and_labels():
    specs = [
        {
            "file": Path("docs/test_query_pipeline.spec.md"),
            "title": "test_query_pipeline.py",
            "tests": [
                {
                    "name": "Retrieves results",
                    "what": "Returns ordered documents",
                    "steps": ["Insert docs", "Run query"],
                }
            ],
        }
    ]

    markdown = export_markdown(specs, get_i18n("es"))

    assert "# Especificaciones de tests" in markdown
    assert "_Generado el " in markdown
    assert "**Que prueba:** Returns ordered documents" in markdown
    assert "**Pasos:**" in markdown


def test_csv_export_localizes_headers():
    specs = [
        {
            "file": Path("docs/test_query_pipeline.spec.md"),
            "title": "test_query_pipeline.py",
            "tests": [
                {
                    "name": "Retrieves results",
                    "what": "Returns ordered documents",
                    "steps": ["Insert docs", "Run query"],
                }
            ],
        }
    ]

    csv_content = export_csv(specs, get_i18n("es"))

    assert csv_content.startswith("Archivo,Test,Que prueba,Pasos")


def test_resolve_language_prefers_explicit_argument(monkeypatch):
    monkeypatch.setenv("PYTEST_TRANSLATOR_LANG", "es_MX.UTF-8")

    assert resolve_language("en") == "en"


def test_resolve_language_prefers_spec_content_over_environment(tmp_path, monkeypatch):
    content = """# test_sample.py

## Acepta etiquetas en espanol
**Qué prueba:** Parsea campos en espanol
**Pasos:**
1. Lee el archivo
"""
    path = tmp_path / "test_sample.spec.md"
    path.write_text(content, encoding="utf-8")
    monkeypatch.setenv("LANG", "en_US.UTF-8")

    assert resolve_language("auto", spec_files=[path]) == "es"


def test_resolve_language_uses_environment_when_auto(monkeypatch):
    monkeypatch.delenv("PYTEST_TRANSLATOR_LANG", raising=False)
    monkeypatch.delenv("LC_ALL", raising=False)
    monkeypatch.setenv("LANG", "es_MX.UTF-8")

    assert resolve_language("auto") == "es"


def test_resolve_language_defaults_to_english(monkeypatch):
    monkeypatch.delenv("PYTEST_TRANSLATOR_LANG", raising=False)
    monkeypatch.delenv("LC_ALL", raising=False)
    monkeypatch.delenv("LANG", raising=False)

    assert resolve_language() == "en"


def test_detect_language_from_text_returns_none_for_ambiguous_content():
    content = """**What it tests:** Works in English
**Qué prueba:** Funciona en espanol
"""

    assert detect_language_from_text(content) is None


def test_get_i18n_uses_gettext_catalogs():
    i18n = get_i18n("es")

    assert i18n.t("app_description") == "Visor interactivo de specs para pytest"


def test_compile_po_file_generates_a_loadable_mo_catalog(tmp_path):
    po_content = """msgid ""
msgstr ""
"Language: es\\n"

msgid "app_description"
msgstr "Descripcion de prueba"
"""
    po_path = tmp_path / "pytest_translator.po"
    po_path.write_text(po_content, encoding="utf-8")

    mo_path = compile_po_file(po_path)

    assert mo_path.exists()
    with mo_path.open("rb") as fh:
        translations = GNUTranslations(fh)
    assert translations.gettext("app_description") == "Descripcion de prueba"


def test_parse_pytest_output_extracts_counts_and_failed_tests():
    output = """============================= test session starts ==============================
collecting ... collected 3 items

tests/test_i18n.py::test_ok PASSED   [ 33%]
tests/test_i18n.py::test_boom FAILED [ 66%]
tests/test_i18n.py::test_skip SKIPPED [100%]

=================== 1 failed, 1 passed, 1 skipped in 0.07s ===================
"""
    report = parse_pytest_output(output)

    assert report["collected"] == 3
    assert report["summary"]["failed"] == 1
    assert report["summary"]["passed"] == 1
    assert report["summary"]["skipped"] == 1
    assert report["duration"] == "0.07s"
    assert [c["nodeid"] for c in report["cases"] if c["status"] == "FAILED"] == [
        "tests/test_i18n.py::test_boom"
    ]


def test_render_natural_pytest_summary_in_spanish():
    report = {
        "collected": 2,
        "cases": [
            {"nodeid": "tests/test_i18n.py::test_ok", "status": "PASSED"},
            {"nodeid": "tests/test_i18n.py::test_boom", "status": "FAILED"},
        ],
        "summary": {"passed": 1, "failed": 1},
        "duration": "0.02s",
    }

    text = render_natural_pytest_summary(report, "es")

    assert "Resumen natural de pytest" in text
    assert "Se recolectaron 2 tests." in text
    assert "1 pasaron, 1 fallaron." in text
    assert "tests/test_i18n.py::test_boom" in text


def test_parse_decorated_spec_file_reads_i18n_metadata(tmp_path):
    test_file = tmp_path / "test_sample.py"
    test_file.write_text(
        """from pytest_translator.decorators import spec

@spec(
    title_en="Handles empty payload",
    title_es="Maneja carga vacia",
    what_en="Returns a controlled error",
    what_es="Regresa un error controlado",
    steps_en=["Send empty payload", "Assert ValueError"],
    steps_es=["Enviar carga vacia", "Validar ValueError"],
)
def test_empty_payload():
    pass
""",
        encoding="utf-8",
    )

    parsed = parse_decorated_spec_file(test_file, "es")

    assert parsed["title"] == "test_sample.py"
    assert parsed["tests"][0]["name"] == "Maneja carga vacia"
    assert parsed["tests"][0]["what"] == "Regresa un error controlado"
    assert parsed["tests"][0]["steps"] == ["Enviar carga vacia", "Validar ValueError"]


def test_load_specs_prefers_decorators_over_spec_markdown(tmp_path):
    test_file = tmp_path / "test_query.py"
    test_file.write_text(
        """from pytest_translator.decorators import spec

@spec(what_en="Decorator source of truth", steps_en=["Step from decorator"])
def test_example():
    pass
""",
        encoding="utf-8",
    )
    spec_file = tmp_path / "test_query.spec.md"
    spec_file.write_text(
        """# test_query.py

## Legacy markdown doc
**What it tests:** Should be ignored when decorator exists
**Steps:**
1. Old step
""",
        encoding="utf-8",
    )

    specs = load_specs(tmp_path, get_i18n("en"))

    assert len(specs) == 1
    assert specs[0]["file"] == test_file
    assert specs[0]["tests"][0]["what"] == "Decorator source of truth"
    assert specs[0]["tests"][0]["steps"] == ["Step from decorator"]


def test_generate_spec_markdown_from_decorators_creates_files(tmp_path):
    test_file = tmp_path / "test_service.py"
    test_file.write_text(
        """from pytest_translator.decorators import spec

@spec(
    title_en="Creates service client",
    what_en="Builds a configured client",
    steps_en=["Load config", "Instantiate client"],
)
def test_build_client():
    pass
""",
        encoding="utf-8",
    )

    generated = generate_spec_markdown_from_decorators(tmp_path, get_i18n("en"))

    assert generated == [tmp_path / "test_service.spec.md"]
    content = generated[0].read_text(encoding="utf-8")
    assert "# test_service.py" in content
    assert "## Creates service client" in content
    assert "**What it tests:** Builds a configured client" in content
