from gettext import GNUTranslations
from pathlib import Path

from pytest_translator.cli import export_csv, export_markdown, parse_spec_file
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
    monkeypatch.setenv("SPECVIEW_LANG", "es_MX.UTF-8")

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
    monkeypatch.delenv("SPECVIEW_LANG", raising=False)
    monkeypatch.delenv("LC_ALL", raising=False)
    monkeypatch.setenv("LANG", "es_MX.UTF-8")

    assert resolve_language("auto") == "es"


def test_resolve_language_defaults_to_english(monkeypatch):
    monkeypatch.delenv("SPECVIEW_LANG", raising=False)
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
    po_path = tmp_path / "specview.po"
    po_path.write_text(po_content, encoding="utf-8")

    mo_path = compile_po_file(po_path)

    assert mo_path.exists()
    with mo_path.open("rb") as fh:
        translations = GNUTranslations(fh)
    assert translations.gettext("app_description") == "Descripcion de prueba"
