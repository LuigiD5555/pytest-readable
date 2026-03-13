import sys
import subprocess
from gettext import GNUTranslations
from pathlib import Path

import pytest_readable.cli as cli
from pytest_readable.compile_locales import compile_po_file
from pytest_readable.core.exporters import render_csv
from pytest_readable.core.models import ReadableSuite, ReadableTestCase
from pytest_readable.core.parser import (
    detect_language_from_decorators,
    find_tests_without_readable,
    parse_decorated_spec_file,
)
from pytest_readable.core.renderer import (
    parse_pytest_output,
    render_summary_text,
    render_markdown,
    render_natural_pytest_summary,
)
from pytest_readable.decorators import readable
from pytest_readable.i18n import get_i18n, resolve_language
from pytest_readable.language_registry import (
    get_language_pack,
    language_pack,
    unregister_language,
)


@readable(
    intention="Whether the markdown export includes a title and timestamp in Spanish.",
    steps=[
        "Build an in-memory suite with a documented case",
        "Run render_markdown with Spanish language",
        "Verify that the title and date marker appear in Spanish",
    ],
    criteria=[
        "The markdown contains a title and timestamp in Spanish",
    ],
)
def test_markdown_export_localizes_title_and_timestamp():
    suite = _build_spanish_documented_suite()
    markdown = render_markdown(suite, "es")
    assert "# Especificaciones de tests" in markdown
    assert "_Generado el " in markdown


@readable(
    intention="Whether the markdown export renders section labels in Spanish.",
    steps=[
        "Build an in-memory suite with a documented case",
        "Run render_markdown with Spanish language",
        "Verify the intention and steps labels in Spanish",
    ],
    criteria=[
        "The section labels are rendered in Spanish",
    ],
)
def test_markdown_export_localizes_section_labels():
    suite = _build_spanish_documented_suite()
    markdown = render_markdown(suite, "es")
    assert "**Si prueba:** Retorna documentos ordenados" in markdown
    assert "**Pasos:**" in markdown


def _build_spanish_documented_suite() -> ReadableSuite:
    return ReadableSuite(
        rootdir=Path("."),
        language="es",
        cases=[
            ReadableTestCase(
                nodeid="tests/test_query.py::test_retrieves_results",
                module_path="tests/test_query.py",
                class_name="",
                function_name="test_retrieves_results",
                display_name="Recupera resultados",
                what="Retorna documentos ordenados",
                steps=["Inserta docs", "Ejecuta query"],
                status="passed",
            )
        ],
    )


@readable(
    intention="Whether the CSV export generates headers translated to the selected language.",
    steps=[
        "Build an in-memory suite",
        "Run render_csv with Spanish language",
        "Verify that the header starts with the expected columns in Spanish",
    ],
    criteria=[
        "The CSV header row matches the localized Spanish columns",
    ],
)
def test_csv_export_localizes_headers():
    suite = _build_spanish_documented_suite()
    csv_content = render_csv(suite, "es")

    assert csv_content.startswith("Archivo,Clase,Test,Si prueba,Pasos,Estado,NodeID")


@readable(
    intention="Whether language resolution uses the explicit argument over environment variables.",
    steps=[
        "Set PYTEST_READABLE_LANG to a Spanish value",
        "Call resolve_language with argument en",
        "Verify that the final result is English",
    ],
    criteria=[
        "resolve_language returns en when it receives the explicit en argument",
    ],
)
def test_resolve_language_prefers_explicit_argument(monkeypatch):
    monkeypatch.setenv("PYTEST_READABLE_LANG", "es_MX.UTF-8")

    assert resolve_language("en") == "en"


@readable(
    intention="Whether auto mode uses the language from the environment.",
    steps=[
        "Set LANG to a Spanish locale",
        "Call resolve_language in auto mode",
        "Verify that the resulting language is Spanish",
    ],
    criteria=[
        "resolve_language detects Spanish from environment variables in auto mode",
    ],
)
def test_resolve_language_uses_environment_when_auto(monkeypatch):
    monkeypatch.delenv("PYTEST_READABLE_LANG", raising=False)
    monkeypatch.delenv("LC_ALL", raising=False)
    monkeypatch.setenv("LANG", "es_MX.UTF-8")

    assert resolve_language("auto") == "es"


@readable(
    intention="Whether language resolution falls back to English when there is no argument or environment variables.",
    steps=[
        "Clear PYTEST_READABLE_LANG, LC_ALL, and LANG",
        "Call resolve_language without arguments",
        "Verify that the result is en",
    ],
    criteria=[
        "resolve_language returns English by default without external configuration",
    ],
)
def test_resolve_language_defaults_to_english(monkeypatch):
    monkeypatch.delenv("PYTEST_READABLE_LANG", raising=False)
    monkeypatch.delenv("LC_ALL", raising=False)
    monkeypatch.delenv("LANG", raising=False)

    assert resolve_language() == "en"


@readable(
    intention="Whether get_i18n obtains real translations from the compiled catalogs.",
    steps=[
        "Request an i18n instance in Spanish",
        "Look up a known translatable key",
        "Verify that the returned text matches the expected translation",
    ],
    criteria=[
        "get_i18n returns the real translation for the requested key",
    ],
)
def test_get_i18n_uses_gettext_catalogs():
    i18n = get_i18n("es")

    assert i18n.t("app_description") == "Visor interactivo de specs para pytest"


@readable(
    intention="Whether language_pack registers a language inheriting non-overridden fields from the base language.",
    steps=[
        "Register a temporary language using language_pack based on English",
        "Look up the registered pack",
        "Verify that non-overridden fields are inherited from the base language",
    ],
    criteria=[
        "The pack inherits non-overridden fields from the base language",
    ],
)
def test_language_pack_decorator_inherits_base_defaults():
    pack = _register_portuguese_test_pack()
    assert pack.markdown_title == "Especificacoes de teste"
    assert pack.markdown_generated_on == "Generated on"


@readable(
    intention="Whether language_pack auto-generates accepted labels from what_label and steps_label.",
    steps=[
        "Register a temporary language using language_pack based on English",
        "Look up the registered pack",
        "Verify the auto-generated accepted labels for what and steps",
    ],
    criteria=[
        "The accepted labels are auto-generated from what_label and steps_label",
    ],
)
def test_language_pack_decorator_autogenerates_accepted_labels():
    pack = _register_portuguese_test_pack()
    assert pack.summary_title == "Resumo legivel"
    assert pack.list_title == "Lista detalhada"
    assert pack.accepted_what_labels == ("**O que testa:**", "**O que testa**:")
    assert pack.accepted_steps_labels == ("**Passos:**", "**Passos**:")


def _register_portuguese_test_pack():
    language_code = "pt_test_registry"
    unregister_language(language_code)

    @language_pack(
        language_code,
        base="en",
        summary_title="Resumo legivel",
        list_title="Lista detalhada",
        what_label="O que testa",
        steps_label="Passos",
        criteria_label="Condicoes de aprovacao",
        status_labels={
            "passed": "aprovadas",
            "failed": "falhadas",
            "skipped": "omitidas",
            "error": "erros",
            "xfailed": "xfalhadas",
            "xpassed": "xaprovadas",
            "collected": "coletadas",
            "unknown": "desconhecido",
        },
    )
    def _register_portuguese_pack():
        return {"markdown_title": "Especificacoes de teste"}

    pack = get_language_pack(language_code)
    unregister_language(language_code)
    return pack


@readable(
    intention="Whether compiling po files generates a valid .mo file.",
    steps=[
        "Create a temporary po file with a simple translation",
        "Run compile_po_file",
        "Verify that the .mo file exists on disk",
    ],
    criteria=[
        "The .mo file is generated correctly",
    ],
)
def test_compile_po_file_generates_mo_file(tmp_path):
    mo_path = _compile_sample_po(tmp_path)
    assert mo_path.exists()


@readable(
    intention="Whether GNUTranslations can load the compiled translation from the .mo file.",
    steps=[
        "Create a temporary po file with a simple translation",
        "Run compile_po_file and open the mo file with GNUTranslations",
        "Verify that the translated key resolves to the expected value",
    ],
    criteria=[
        "GNUTranslations can read the expected translation",
    ],
)
def test_compile_po_file_loads_translation_catalog(tmp_path):
    mo_path = _compile_sample_po(tmp_path)
    with mo_path.open("rb") as fh:
        translations = GNUTranslations(fh)
    assert translations.gettext("app_description") == "Descripcion de prueba"


def _compile_sample_po(tmp_path: Path) -> Path:
    po_content = """msgid ""
msgstr ""
"Language: es\\n"

msgid "app_description"
msgstr "Descripcion de prueba"
"""
    po_path = tmp_path / "pytest_readable.po"
    po_path.write_text(po_content, encoding="utf-8")

    return compile_po_file(po_path)


@readable(
    intention="Whether parse_pytest_output extracts counts and duration from the pytest summary.",
    steps=[
        "Prepare sample pytest output with PASSED, FAILED, and SKIPPED cases",
        "Run parse_pytest_output",
        "Verify the collected count, summary counts, and duration",
    ],
    criteria=[
        "The parser returns the correct counts and duration",
    ],
)
def test_parse_pytest_output_extracts_counts_and_duration():
    report = _parse_sample_pytest_output()
    assert report["collected"] == 3
    assert report["summary"]["failed"] == 1
    assert report["summary"]["passed"] == 1
    assert report["summary"]["skipped"] == 1
    assert report["duration"] == "0.07s"


@readable(
    intention="Whether parse_pytest_output identifies the failed nodeid in the parsed cases.",
    steps=[
        "Prepare sample pytest output with PASSED, FAILED, and SKIPPED cases",
        "Run parse_pytest_output",
        "Verify that the FAILED case nodeid is identified",
    ],
    criteria=[
        "The failed nodeid is identified in the parsed output",
    ],
)
def test_parse_pytest_output_extracts_failed_nodeid():
    report = _parse_sample_pytest_output()
    assert [c["nodeid"] for c in report["cases"] if c["status"] == "FAILED"] == [
        "tests/test_i18n.py::test_boom"
    ]


def _parse_sample_pytest_output():
    output = """============================= test session starts ==============================
collecting ... collected 3 items

tests/test_i18n.py::test_ok PASSED   [ 33%]
tests/test_i18n.py::test_boom FAILED [ 66%]
tests/test_i18n.py::test_skip SKIPPED [100%]

=================== 1 failed, 1 passed, 1 skipped in 0.07s ===================
"""
    return parse_pytest_output(output)


@readable(
    intention="Whether render_natural_pytest_summary shows the header and counts in Spanish.",
    steps=[
        "Build an in-memory parsed report with one passing and one failing test",
        "Run render_natural_pytest_summary with language es",
        "Verify the localized header and counts",
    ],
    criteria=[
        "The report includes the header and status summary in Spanish",
    ],
)
def test_render_natural_pytest_summary_localizes_header_and_counts():
    text = _render_sample_natural_summary_es()
    assert "Resumen natural de pytest" in text
    assert "Se recolectaron 2 tests." in text
    assert "1 pasaron, 1 fallaron." in text


@readable(
    intention="Whether render_natural_pytest_summary includes the failed nodeid in the final details.",
    steps=[
        "Build an in-memory parsed report with one passing and one failing test",
        "Run render_natural_pytest_summary with language es",
        "Verify that the failed nodeid appears in the final details",
    ],
    criteria=[
        "The failing test is listed in the final details",
    ],
)
def test_render_natural_pytest_summary_lists_failed_nodeid():
    text = _render_sample_natural_summary_es()
    assert "tests/test_i18n.py::test_boom" in text


def _render_sample_natural_summary_es():
    report = {
        "collected": 2,
        "cases": [
            {"nodeid": "tests/test_i18n.py::test_ok", "status": "PASSED"},
            {"nodeid": "tests/test_i18n.py::test_boom", "status": "FAILED"},
        ],
        "summary": {"passed": 1, "failed": 1},
        "duration": "0.02s",
    }
    return render_natural_pytest_summary(report, "es")


@readable(
    intention="Whether render_summary_text in Spanish uses localized detail labels.",
    steps=[
        "Build an in-memory suite with a passing case, description, and steps",
        "Run render_summary_text with Spanish language and step inclusion",
        "Verify the header, counts, and localized labels",
    ],
    criteria=[
        "The summary uses detail labels in Spanish",
    ],
)
def test_render_summary_text_spanish_uses_localized_labels():
    text = _render_spanish_detailed_summary()
    assert "Resumen legible" in text
    assert "- aprobadas: 1" in text
    assert "Lista detallada" in text
    assert "[aprobadas] tests/test_demo.py::test_ok" in text
    assert "Qué prueba: Valida caso correcto" in text
    assert "Pasos:" in text
    assert "Condiciones para aprobar:" in text


@readable(
    intention="Whether render_summary_text in Spanish shows steps, criteria, and the case final summary.",
    steps=[
        "Build an in-memory suite with a passing case, description, and steps",
        "Run render_summary_text with Spanish language and step inclusion",
        "Verify the steps, criteria, and final report summary",
    ],
    criteria=[
        "The case steps and criteria are rendered",
    ],
)
def test_render_summary_text_spanish_renders_steps_and_criteria():
    text = _render_spanish_detailed_summary()
    assert "1. Retorna estado aprobado" in text
    assert "Resumen final: total=1, aprobadas=1, fallidas=0, omitidas=0" in text


@readable(
    intention="Whether render_summary_text preserves language-specific labels for Spanish and English cases.",
    steps=[
        "Build a suite with one case in Spanish and another in English",
        "Run render_summary_text in detailed mode",
        "Verify the status, intention, and step labels for each language",
    ],
    criteria=[
        "Each case preserves its language labels for status, intention, and steps",
    ],
)
def test_render_summary_text_uses_case_language_labels():
    text = _render_mixed_language_summary()
    assert "Resumen legible" in text
    assert "[aprobadas] tests/test_demo.py::test_es" in text
    assert "[passed] tests/test_demo.py::test_en" in text
    assert "Qué prueba: Valida salida" in text
    assert "Pasos:" in text
    assert "What it tests: Validates output" in text
    assert "Steps:" in text


@readable(
    intention="Whether render_summary_text shows localized placeholders when criteria are missing.",
    steps=[
        "Build a suite with one Spanish case and one English case without criteria",
        "Run render_summary_text in detailed mode",
        "Verify the criteria placeholders in Spanish and English",
    ],
    criteria=[
        "A localized placeholder is shown when criteria are missing",
    ],
)
def test_render_summary_text_uses_localized_missing_criteria_placeholders():
    text = _render_mixed_language_summary()
    assert "Condiciones para aprobar:" in text
    assert "1. Sin criterios documentados" in text
    assert "Pass conditions:" in text
    assert "1. No pass conditions documented" in text


@readable(
    intention="Whether parse_decorated_spec_file selects Spanish metadata for the requested language.",
    steps=[
        "Create a temporary file with readable and title, intention, and steps fields in English and Spanish",
        "Run parse_decorated_spec_file with Spanish language",
        "Verify that the result uses the name and intention in Spanish",
    ],
    criteria=[
        "parse_decorated_spec_file selects Spanish metadata",
    ],
)
def test_parse_decorated_spec_file_selects_spanish_metadata(tmp_path):
    parsed = _parse_i18n_decorated_spec(tmp_path)
    assert parsed["title"] == "test_sample.py"
    assert parsed["tests"][0]["name"] == "Maneja carga vacia"
    assert parsed["tests"][0]["what"] == "Regresa un error controlado"


@readable(
    intention="Whether parse_decorated_spec_file preserves i18n steps and criteria as lists.",
    steps=[
        "Create a temporary file with readable and i18n fields for steps and criteria",
        "Run parse_decorated_spec_file with Spanish language",
        "Verify that steps and criteria are preserved as lists",
    ],
    criteria=[
        "The steps and criteria are preserved as lists",
    ],
)
def test_parse_decorated_spec_file_preserves_i18n_lists(tmp_path):
    parsed = _parse_i18n_decorated_spec(tmp_path)
    assert parsed["tests"][0]["steps"] == ["Enviar carga vacia", "Validar ValueError"]
    assert parsed["tests"][0]["criteria"] == ["Lanza ValueError", "Registra el error"]


def _render_spanish_detailed_summary() -> str:
    suite = ReadableSuite(
        rootdir=Path("."),
        language="es",
        cases=[
            ReadableTestCase(
                nodeid="tests/test_demo.py::test_ok",
                module_path="tests/test_demo.py",
                class_name="",
                function_name="test_ok",
                display_name="ok",
                what="Valida caso correcto",
                steps=["Prepara entrada", "Valida salida"],
                criteria=["Retorna estado aprobado", "No lanza excepciones"],
                status="passed",
            )
        ],
    )
    return render_summary_text(suite, "es", include_steps=True)


def _render_mixed_language_summary() -> str:
    suite = ReadableSuite(
        rootdir=Path("."),
        language="es",
        cases=[
            ReadableTestCase(
                nodeid="tests/test_demo.py::test_es",
                module_path="tests/test_demo.py",
                class_name="",
                function_name="test_es",
                display_name="caso espanol",
                language="es",
                what="Valida salida",
                steps=["Corre flujo"],
                status="passed",
            ),
            ReadableTestCase(
                nodeid="tests/test_demo.py::test_en",
                module_path="tests/test_demo.py",
                class_name="",
                function_name="test_en",
                display_name="english case",
                language="en",
                what="Validates output",
                steps=["Run flow"],
                status="passed",
            ),
        ],
    )
    return render_summary_text(suite, "es", include_steps=True)


def _parse_i18n_decorated_spec(tmp_path: Path) -> dict:
    test_file = tmp_path / "test_sample.py"
    test_file.write_text(
        """from pytest_readable.decorators import readable

@readable(
    title_en="Handles empty payload",
    title_es="Maneja carga vacia",
    intention_en="Returns a controlled error",
    intention_es="Regresa un error controlado",
    steps_en=["Send empty payload", "Assert ValueError"],
    steps_es=["Enviar carga vacia", "Validar ValueError"],
    criteria_en=["Raises ValueError", "Logs the error"],
    criteria_es=["Lanza ValueError", "Registra el error"],
)
def test_empty_payload():
    pass
""",
        encoding="utf-8",
    )
    return parse_decorated_spec_file(test_file, "es")


@readable(
    intention="Whether parse_decorated_spec_file extracts the expected intention and title from @readable.",
    steps=[
        "Create a temporary file with readable, intention, and multiline steps",
        "Run parse_decorated_spec_file in English",
        "Verify the extracted title, case name, and intention",
    ],
    criteria=[
        "The intention and title are extracted with the expected values",
    ],
)
def test_parse_decorated_spec_file_extracts_intention_and_title(tmp_path):
    parsed = _parse_readable_multiline_steps_file(tmp_path)
    assert parsed["title"] == "test_sample.py"
    assert parsed["tests"][0]["name"] == "test_sample.py"
    assert parsed["tests"][0]["what"] == "Parses english fields"


@readable(
    intention="Whether parse_decorated_spec_file normalizes numbered multiline steps into an ordered list.",
    steps=[
        "Create a temporary file with readable, intention, and multiline steps",
        "Run parse_decorated_spec_file in English",
        "Verify that the steps are normalized into an ordered list",
    ],
    criteria=[
        "The parser normalizes multiline steps into an ordered list",
    ],
)
def test_parse_decorated_spec_file_normalizes_multiline_steps(tmp_path):
    parsed = _parse_readable_multiline_steps_file(tmp_path)
    assert parsed["tests"][0]["steps"] == ["Read the file", "Extract the fields"]


def _parse_readable_multiline_steps_file(tmp_path: Path) -> dict:
    test_file = tmp_path / "test_sample.py"
    test_file.write_text(
        '''from pytest_readable.decorators import readable

@readable(
    title="test_sample.py",
    intention="Parses english fields",
    steps="""
1. Read the file
2. Extract the fields
""",
)
def test_parse_readable_metadata_accepts_english_labels():
    pass
''',
        encoding="utf-8",
    )
    return parse_decorated_spec_file(test_file, "en")


@readable(
    intention="Whether the readable decorator preserves the expected intention and title in metadata.",
    steps=[
        "Define a test decorated with readable using intention and multiline steps",
        "Read __spec_meta__ from the decorated function",
        "Verify that title and intention are stored with the expected values",
    ],
    criteria=[
        "The stored metadata preserves the expected intention and title",
    ],
)
def test_readable_decorator_preserves_intention_and_title():
    metadata = _build_readable_metadata_from_multiline_strings()
    assert metadata["title"] == "test_sample.py"
    assert metadata["intention"] == "Parses english fields"


@readable(
    intention="Whether the readable decorator normalizes steps and criteria when they are defined as multiline text.",
    steps=[
        "Define a test decorated with readable using intention and steps/criteria as text",
        "Read __spec_meta__ from the decorated function",
        "Verify that steps and criteria are normalized into clean lists",
    ],
    criteria=[
        "The decorator normalizes steps and criteria into clean lists",
    ],
)
def test_readable_decorator_normalizes_steps_and_criteria_lists():
    metadata = _build_readable_metadata_from_multiline_strings()
    assert metadata["steps"] == ["Read the file", "Extract the fields"]
    assert metadata["criteria"] == ["Returns expected fields", "No parsing errors"]


def _build_readable_metadata_from_multiline_strings() -> dict:
    @readable(
        title="test_sample.py",
        intention="Parses english fields",
        steps="""
1. Read the file
2. Extract the fields
""",
        criteria="""
1. Returns expected fields
2. No parsing errors
""",
    )
    def test_parse_readable_metadata_accepts_english_labels():
        return None

    return test_parse_readable_metadata_accepts_english_labels.__spec_meta__


@readable(
    intention="Whether detect_language_from_decorators returns None when the languages tie.",
    steps=[
        "Create two test files, one with metadata in English and one in Spanish",
        "Run detect_language_from_decorators on the directory",
        "Verify that it returns None because the scores tie",
    ],
    criteria=[
        "The detector ignores cases where no language predominates",
    ],
)
def test_detect_language_from_decorators_returns_none_on_tie(tmp_path):
    en_file = tmp_path / "test_english.py"
    en_file.write_text(
        """from pytest_readable.decorators import readable

@readable(intention_en="English metadata")
def test_english():
    pass
""",
        encoding="utf-8",
    )
    es_file = tmp_path / "test_spanish.py"
    es_file.write_text(
        """from pytest_readable.decorators import readable

@readable(intention_es="Metadata en español")
def test_spanish():
    pass
""",
        encoding="utf-8",
    )

    assert detect_language_from_decorators(tmp_path) is None


@readable(
    intention="Whether detect_language_from_decorators prioritizes Spanish when there are hints in that language.",
    steps=[
        "Create a file with metadata that uses accents and Spanish labels",
        "Run detect_language_from_decorators on the directory",
        "Confirm that it returns 'es' because Spanish tokens dominate",
    ],
    criteria=[
        "The linguistic hints cause Spanish to be chosen in auto mode",
    ],
)
def test_detect_language_from_decorators_prefers_spanish(tmp_path):
    spanish_file = tmp_path / "test_spanish_tokens.py"
    spanish_file.write_text(
        """from pytest_readable.decorators import readable

@readable(
    intention="Valida Qué prueba y Pasos para detectar español",
    steps=[
        "Qué prueba: describe el flujo español",
        "Pasos: confirma la detección automática",
    ],
)
def test_spanish_tokens():
    pass
""",
        encoding="utf-8",
    )

    assert detect_language_from_decorators(tmp_path) == "es"


@readable(
    intention="Verifica que se detecte la metadata readable faltante para pruebas de módulo y clase.",
    steps=[
        "Crea archivos de prueba con funciones decoradas y no decoradas",
        "Ejecuta find_tests_without_readable sobre el directorio temporal",
        "Verifica que solo se reporten las pruebas no decoradas",
    ],
    criteria=[
        "El resultado contiene exactamente las funciones de prueba sin el decorador readable",
    ],
)
def test_find_tests_without_readable_reports_missing_functions(tmp_path):
    test_file = tmp_path / "test_sample.py"
    test_file.write_text(
        """from pytest_readable.decorators import readable

@readable(
    intention="Documented",
    steps=["Step one"],
)
def test_documented():
    pass

def test_missing_case():
    pass
""",
        encoding="utf-8",
    )
    class_file = tmp_path / "test_class_case.py"
    class_file.write_text(
        """from pytest_readable.decorators import readable

class TestFlow:
    @readable(
        intention="Documented method",
        steps=["Step one"],
    )
    def test_documented_method(self):
        pass

    def test_missing_method(self):
        pass
""",
        encoding="utf-8",
    )

    missing = find_tests_without_readable(tmp_path)
    normalized = [(str(path.relative_to(tmp_path)), name) for path, name in missing]
    assert normalized == [
        ("test_class_case.py", "TestFlow.test_missing_method"),
        ("test_sample.py", "test_missing_case"),
    ]


@readable(
    intention="Verifica que el modo missing-readable del CLI reporte pruebas faltantes y omita la ejecución de pytest.",
    steps=[
        "Crea una prueba temporal sin @readable",
        "Intercepta subprocess.run para impedir la ejecución real de pytest",
        "Ejecuta cli.main con --find-missing y valida la salida",
    ],
    criteria=[
        "El CLI devuelve fallo y lista las pruebas faltantes sin llamar a subprocess.run",
    ],
)
def test_cli_find_missing_skips_pytest_execution(monkeypatch, tmp_path, capsys):
    test_file = tmp_path / "test_plain.py"
    test_file.write_text(
        """
def test_without_readable():
    pass
""",
        encoding="utf-8",
    )

    def fail_if_called(*args, **kwargs):
        raise AssertionError("subprocess.run should not be called in --find-missing mode")

    monkeypatch.setattr(cli.subprocess, "run", fail_if_called)
    code = cli.main(["--find-missing", f"--tests-root={tmp_path}"])
    rendered = capsys.readouterr().out

    assert code == 1
    assert "Functions missing @readable:" in rendered
    assert "test_plain.py:test_without_readable" in rendered


@readable(
    intention="Whether the readable wrapper removes the redundant positional pytest token from the command.",
    steps=[
        "Intercept subprocess.run from the CLI",
        "Run main with pytest and q arguments",
        "Verify that the final command does not include the redundant token",
    ],
    criteria=[
        "The final command removes the redundant pytest token",
    ],
)
def test_cli_ignores_leading_pytest_token_in_forwarded_command(monkeypatch):
    code, captured = _run_cli_main_with_leading_pytest(monkeypatch)
    assert code == 0
    assert captured["command"] == [sys.executable, "-m", "pytest", "--readable", "-q", "--color=yes"]


@readable(
    intention="Whether the readable wrapper enables the expected readable flags and capture options.",
    steps=[
        "Intercept subprocess.run from the CLI",
        "Run main with pytest and q arguments",
        "Verify text mode, output capture, and disabled check",
    ],
    criteria=[
        "The expected readable flags and capture options are enabled",
    ],
)
def test_cli_ignores_leading_pytest_token_enables_expected_capture_flags(monkeypatch):
    code, captured = _run_cli_main_with_leading_pytest(monkeypatch)
    assert code == 0
    assert captured["text"] is True
    assert captured["capture_output"] is True
    assert captured["check"] is False


def _run_cli_main_with_leading_pytest(monkeypatch):
    captured: dict[str, list[str] | bool | str] = {}

    def fake_run(command: list[str], *, text: bool, capture_output: bool, check: bool) -> subprocess.CompletedProcess:
        captured["command"] = command
        captured["text"] = text
        captured["capture_output"] = capture_output
        captured["check"] = check
        return subprocess.CompletedProcess(command, 0, stdout="Resumen legible\n- Total: 0\n", stderr="")

    monkeypatch.setattr(cli.subprocess, "run", fake_run)

    code = cli.main(["pytest", "-q"])
    return code, captured


@readable(
    intention="Whether readable pytest --lang=es forwards the language to the final command.",
    steps=[
        "Intercept subprocess.run from the CLI",
        "Run main with pytest and lang es arguments",
        "Verify that the final command includes readable-lang=es",
    ],
    criteria=[
        "The final command includes readable-lang=es",
    ],
)
def test_cli_forwards_lang_to_pytest_command(monkeypatch):
    code, captured_command = _run_cli_main_with_lang_es(monkeypatch)
    assert code == 0
    assert "--readable-lang=es" in captured_command


@readable(
    intention="Whether readable pytest --lang=es runs in summary mode without forcing detail flags.",
    steps=[
        "Intercept subprocess.run from the CLI",
        "Run main with pytest and lang es arguments",
        "Verify readable-lang and color without forcing detail flags",
    ],
    criteria=[
        "The final command uses --readable without additional detail flags",
    ],
)
def test_cli_forwards_lang_without_forcing_quiet_defaults(monkeypatch):
    code, captured_command = _run_cli_main_with_lang_es(monkeypatch)
    assert code == 0
    assert captured_command == [
        sys.executable,
        "-m",
        "pytest",
        "--readable",
        "--readable-lang=es",
        "--color=yes",
    ]


@readable(
    intention="Whether readable pytest -v enables readable-verbose while still forwarding pytest verbosity.",
    steps=[
        "Intercept subprocess.run from the CLI",
        "Run main with pytest and -v arguments",
        "Verify that the final command keeps -v and adds --readable-verbose",
    ],
    criteria=[
        "The final command includes -v and --readable-verbose",
    ],
)
def test_cli_maps_short_verbose_flag_to_readable_verbose(monkeypatch):
    code, captured_command = _run_cli_main_with_verbose(monkeypatch, "-v")
    assert code == 0
    assert captured_command == [
        sys.executable,
        "-m",
        "pytest",
        "-v",
        "--readable-verbose",
        "--color=yes",
    ]


@readable(
    intention="Whether readable pytest --verbose enables readable-verbose while still forwarding pytest verbosity.",
    steps=[
        "Intercept subprocess.run from the CLI",
        "Run main with pytest and --verbose arguments",
        "Verify that the final command keeps --verbose and adds --readable-verbose",
    ],
    criteria=[
        "The final command includes --verbose and --readable-verbose",
    ],
)
def test_cli_maps_long_verbose_flag_to_readable_verbose(monkeypatch):
    code, captured_command = _run_cli_main_with_verbose(monkeypatch, "--verbose")
    assert code == 0
    assert captured_command == [
        sys.executable,
        "-m",
        "pytest",
        "--verbose",
        "--readable-verbose",
        "--color=yes",
    ]


@readable(
    intention="Whether readable pytest --detailed enables readable-detailed as an explicit mode.",
    steps=[
        "Intercept subprocess.run from the CLI",
        "Run main with pytest and detailed arguments",
        "Verify that the final command uses readable-detailed",
    ],
    criteria=[
        "The final command includes --readable-detailed and does not keep --readable",
    ],
)
def test_cli_maps_detailed_flag_to_readable_detailed(monkeypatch):
    captured: dict[str, list[str]] = {}

    def fake_run(command: list[str], *, text: bool, capture_output: bool, check: bool) -> subprocess.CompletedProcess:
        captured["command"] = command
        return subprocess.CompletedProcess(command, 0, stdout="Readable summary\n- Total: 0\n", stderr="")

    monkeypatch.setattr(cli.subprocess, "run", fake_run)

    code = cli.main(["pytest", "--detailed"])
    assert code == 0
    assert captured["command"] == [
        sys.executable,
        "-m",
        "pytest",
        "--readable-detailed",
        "--color=yes",
    ]


@readable(
    intention="Whether readable pytest -d enables readable-detailed as the short alias for detailed mode.",
    steps=[
        "Intercept subprocess.run from the CLI",
        "Run main with pytest and d arguments",
        "Verify that the final command uses readable-detailed",
    ],
    criteria=[
        "The final command includes --readable-detailed",
    ],
)
def test_cli_maps_short_detailed_flag_to_readable_detailed(monkeypatch):
    captured: dict[str, list[str]] = {}

    def fake_run(command: list[str], *, text: bool, capture_output: bool, check: bool) -> subprocess.CompletedProcess:
        captured["command"] = command
        return subprocess.CompletedProcess(command, 0, stdout="Readable summary\n- Total: 0\n", stderr="")

    monkeypatch.setattr(cli.subprocess, "run", fake_run)

    code = cli.main(["pytest", "-d"])
    assert code == 0
    assert captured["command"] == [
        sys.executable,
        "-m",
        "pytest",
        "--readable-detailed",
        "--color=yes",
    ]


@readable(
    intention="Whether readable pytest -detailed enables readable-detailed as the extended short alias for detailed mode.",
    steps=[
        "Intercept subprocess.run from the CLI",
        "Run main with pytest and short-prefixed detailed arguments",
        "Verify that the final command uses readable-detailed",
    ],
    criteria=[
        "The final command includes --readable-detailed",
    ],
)
def test_cli_maps_extended_short_detailed_flag_to_readable_detailed(monkeypatch):
    captured: dict[str, list[str]] = {}

    def fake_run(command: list[str], *, text: bool, capture_output: bool, check: bool) -> subprocess.CompletedProcess:
        captured["command"] = command
        return subprocess.CompletedProcess(command, 0, stdout="Readable summary\n- Total: 0\n", stderr="")

    monkeypatch.setattr(cli.subprocess, "run", fake_run)

    code = cli.main(["pytest", "-detailed"])
    assert code == 0
    assert captured["command"] == [
        sys.executable,
        "-m",
        "pytest",
        "--readable-detailed",
        "--color=yes",
    ]


def _run_cli_main_with_lang_es(monkeypatch):
    captured: dict[str, list[str]] = {}

    def fake_run(command: list[str], *, text: bool, capture_output: bool, check: bool) -> subprocess.CompletedProcess:
        captured["command"] = command
        return subprocess.CompletedProcess(command, 0, stdout="Resumen legible\n- Total: 0\n", stderr="")

    monkeypatch.setattr(cli.subprocess, "run", fake_run)

    code = cli.main(["pytest", "--lang=es"])
    return code, captured["command"]


def _run_cli_main_with_verbose(monkeypatch, verbose_flag: str):
    captured: dict[str, list[str]] = {}

    def fake_run(command: list[str], *, text: bool, capture_output: bool, check: bool) -> subprocess.CompletedProcess:
        captured["command"] = command
        return subprocess.CompletedProcess(command, 0, stdout="Readable summary\n- Total: 0\n", stderr="")

    monkeypatch.setattr(cli.subprocess, "run", fake_run)

    code = cli.main(["pytest", verbose_flag])
    return code, captured["command"]


@readable(
    intention="Whether the readable wrapper keeps relevant failure sections when filtering output.",
    steps=[
        "Simulate output with FAILURES, warnings, short summary, and a readable block",
        "Run the CLI filtered printer",
        "Verify that relevant sections are included in the rendered output",
    ],
    criteria=[
        "Relevant failure sections and the readable block are preserved",
    ],
)
def test_cli_prints_relevant_sections_when_pytest_fails(capsys):
    rendered = _render_filtered_cli_failure_output(capsys)
    assert "FAILURES" in rendered
    assert "warnings summary" in rendered
    assert "short test summary info" in rendered
    assert "Resumen legible" in rendered


@readable(
    intention="Whether the readable wrapper omits the final raw pytest summary line when filtering failures.",
    steps=[
        "Simulate output with FAILURES, warnings, short summary, and a readable block",
        "Run the CLI filtered printer",
        "Verify that the final raw summary line is not printed",
    ],
    criteria=[
        "The final raw pytest summary line is not printed",
    ],
)
def test_cli_does_not_print_raw_final_pytest_summary_on_failure(capsys):
    rendered = _render_filtered_cli_failure_output(capsys)
    assert "1 failed in 0.01s" not in rendered


def _render_filtered_cli_failure_output(capsys) -> str:
    output = """
============================= FAILURES =============================
_______________________________ test_boom _______________________________
E   AssertionError: boom

============================= warnings summary =============================
test_x.py:1: UserWarning: sample

=========================== short test summary info ===========================
FAILED test_x.py::test_boom - AssertionError: boom

Resumen legible

- Total: 1
- fallidas: 1

Lista legible

- [fallidas] test_x.py::test_boom
    Qué prueba: Falla al validar

1 failed in 0.01s
""".strip()

    cli._print_wrapped_output(output, "", 1)
    return capsys.readouterr().out
