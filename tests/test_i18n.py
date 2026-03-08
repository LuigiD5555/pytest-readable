import os
import tempfile
import unittest
from gettext import GNUTranslations
from pathlib import Path
from unittest import mock

from pytest_specview.cli import export_csv, export_markdown, parse_spec_file
from pytest_specview.compile_locales import compile_po_file
from pytest_specview.i18n import detect_language_from_text, get_i18n, resolve_language


class BilingualParsingTests(unittest.TestCase):
    def test_parse_spec_file_accepts_english_labels(self):
        content = """# test_sample.py

## Handles english labels
**What it tests:** Parses english fields
**Steps:**
1. Read the file
2. Extract the fields
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test_sample.spec.md"
            path.write_text(content, encoding="utf-8")

            spec = parse_spec_file(path, get_i18n("en"))

        self.assertEqual(spec["title"], "test_sample.py")
        self.assertEqual(spec["tests"][0]["what"], "Parses english fields")
        self.assertEqual(spec["tests"][0]["steps"], ["Read the file", "Extract the fields"])

    def test_parse_spec_file_accepts_spanish_labels(self):
        content = """# test_sample.py

## Acepta etiquetas en espanol
**Qué prueba:** Parsea campos en espanol
**Pasos:**
1. Lee el archivo
2. Extrae los campos
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test_sample.spec.md"
            path.write_text(content, encoding="utf-8")

            spec = parse_spec_file(path, get_i18n("es"))

        self.assertEqual(spec["title"], "test_sample.py")
        self.assertEqual(spec["tests"][0]["what"], "Parsea campos en espanol")
        self.assertEqual(spec["tests"][0]["steps"], ["Lee el archivo", "Extrae los campos"])


class LocalizationOutputTests(unittest.TestCase):
    def setUp(self):
        self.specs = [
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

    def test_markdown_export_localizes_title_and_labels(self):
        markdown = export_markdown(self.specs, get_i18n("es"))

        self.assertIn("# Especificaciones de tests", markdown)
        self.assertIn("_Generado el ", markdown)
        self.assertIn("**Que prueba:** Returns ordered documents", markdown)
        self.assertIn("**Pasos:**", markdown)

    def test_csv_export_localizes_headers(self):
        csv_content = export_csv(self.specs, get_i18n("es"))

        self.assertTrue(csv_content.startswith("Archivo,Test,Que prueba,Pasos"))


class LanguageResolutionTests(unittest.TestCase):
    def test_resolve_language_prefers_explicit_argument(self):
        with mock.patch.dict(os.environ, {"SPECVIEW_LANG": "es_MX.UTF-8"}, clear=True):
            self.assertEqual(resolve_language("en"), "en")

    def test_resolve_language_prefers_spec_content_over_environment(self):
        content = """# test_sample.py

## Acepta etiquetas en espanol
**Qué prueba:** Parsea campos en espanol
**Pasos:**
1. Lee el archivo
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test_sample.spec.md"
            path.write_text(content, encoding="utf-8")

            with mock.patch.dict(os.environ, {"LANG": "en_US.UTF-8"}, clear=True):
                self.assertEqual(resolve_language("auto", spec_files=[path]), "es")

    def test_resolve_language_uses_environment_when_auto(self):
        with mock.patch.dict(os.environ, {"LANG": "es_MX.UTF-8"}, clear=True):
            self.assertEqual(resolve_language("auto"), "es")

    def test_resolve_language_defaults_to_english(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertEqual(resolve_language(), "en")

    def test_detect_language_from_text_returns_none_for_ambiguous_content(self):
        content = """**What it tests:** Works in English
**Qué prueba:** Funciona en espanol
"""
        self.assertIsNone(detect_language_from_text(content))

    def test_get_i18n_uses_gettext_catalogs(self):
        i18n = get_i18n("es")
        self.assertEqual(i18n.t("app_description"), "Visor interactivo de specs para pytest")


class LocaleCompilationTests(unittest.TestCase):
    def test_compile_po_file_generates_a_loadable_mo_catalog(self):
        po_content = """msgid ""
msgstr ""
"Language: es\\n"

msgid "app_description"
msgstr "Descripcion de prueba"
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            po_path = Path(tmpdir) / "specview.po"
            po_path.write_text(po_content, encoding="utf-8")

            mo_path = compile_po_file(po_path)

            self.assertTrue(mo_path.exists())
            with mo_path.open("rb") as fh:
                translations = GNUTranslations(fh)
            self.assertEqual(translations.gettext("app_description"), "Descripcion de prueba")


if __name__ == "__main__":
    unittest.main()
