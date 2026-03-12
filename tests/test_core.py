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
    intention="Si la exportacion markdown incluye titulo y marca temporal en español.",
    steps=[
        "Construye una suite en memoria con un caso documentado",
        "Ejecuta render_markdown con idioma español",
        "Verifica presencia de titulo y marca de fecha en español",
    ],
    criteria=[
        "El markdown contiene titulo y marca temporal en español",
    ],
)
def test_markdown_export_localizes_title_and_timestamp():
    suite = _build_spanish_documented_suite()
    markdown = render_markdown(suite, "es")
    assert "# Especificaciones de tests" in markdown
    assert "_Generado el " in markdown


@readable(
    intention="Si la exportacion markdown renderiza labels de seccion en español.",
    steps=[
        "Construye una suite en memoria con un caso documentado",
        "Ejecuta render_markdown con idioma español",
        "Verifica labels de intención y pasos en español",
    ],
    criteria=[
        "Los labels de seccion se renderizan en español",
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
    intention="Si la exportacion csv genera encabezados traducidos al idioma seleccionado.",
    steps=[
        "Construye una suite en memoria",
        "Ejecuta render_csv con idioma español",
        "Verifica que el encabezado inicia con columnas esperadas en español",
    ],
    criteria=[
        "La fila de encabezado CSV coincide con columnas localizadas en español",
    ],
)
def test_csv_export_localizes_headers():
    suite = _build_spanish_documented_suite()
    csv_content = render_csv(suite, "es")

    assert csv_content.startswith("Archivo,Clase,Test,Si prueba,Pasos,Estado,NodeID")


@readable(
    intention="Si la resolucion de idioma usa el argumento explicito por encima de variables de entorno.",
    steps=[
        "Define PYTEST_READABLE_LANG con valor español",
        "Llama resolve_language con argumento en",
        "Verifica que el resultado final sea ingles",
    ],
    criteria=[
        "resolve_language retorna en cuando recibe argumento explicito en",
    ],
)
def test_resolve_language_prefers_explicit_argument(monkeypatch):
    monkeypatch.setenv("PYTEST_READABLE_LANG", "es_MX.UTF-8")

    assert resolve_language("en") == "en"


@readable(
    intention="Si en modo auto se usa el idioma del entorno.",
    steps=[
        "Define LANG con una localidad en español",
        "Llama resolve_language en auto",
        "Verifica que el idioma resultante sea español",
    ],
    criteria=[
        "resolve_language detecta español desde variables de entorno en modo auto",
    ],
)
def test_resolve_language_uses_environment_when_auto(monkeypatch):
    monkeypatch.delenv("PYTEST_READABLE_LANG", raising=False)
    monkeypatch.delenv("LC_ALL", raising=False)
    monkeypatch.setenv("LANG", "es_MX.UTF-8")

    assert resolve_language("auto") == "es"


@readable(
    intention="Si la resolucion de idioma vuelve a ingles cuando no hay argumento ni variables de entorno.",
    steps=[
        "Limpia PYTEST_READABLE_LANG, LC_ALL y LANG",
        "Llama resolve_language sin argumentos",
        "Verifica que el resultado sea en",
    ],
    criteria=[
        "resolve_language retorna ingles por defecto sin configuracion externa",
    ],
)
def test_resolve_language_defaults_to_english(monkeypatch):
    monkeypatch.delenv("PYTEST_READABLE_LANG", raising=False)
    monkeypatch.delenv("LC_ALL", raising=False)
    monkeypatch.delenv("LANG", raising=False)

    assert resolve_language() == "en"


@readable(
    intention="Si get_i18n obtiene traducciones reales desde los catalogos compilados.",
    steps=[
        "Solicita instancia i18n en español",
        "Consulta una clave traducible conocida",
        "Verifica que el texto retornado sea la traduccion esperada",
    ],
    criteria=[
        "get_i18n retorna traduccion real para la clave consultada",
    ],
)
def test_get_i18n_uses_gettext_catalogs():
    i18n = get_i18n("es")

    assert i18n.t("app_description") == "Visor interactivo de specs para pytest"


@readable(
    intention="Si language_pack registra un idioma heredando campos no sobreescritos del base.",
    steps=[
        "Registra un idioma temporal usando language_pack con base en ingles",
        "Consulta el pack registrado",
        "Verifica herencia de campos no sobreescritos desde el idioma base",
    ],
    criteria=[
        "El pack hereda campos no sobreescritos del idioma base",
    ],
)
def test_language_pack_decorator_inherits_base_defaults():
    pack = _register_portuguese_test_pack()
    assert pack.markdown_title == "Especificacoes de teste"
    assert pack.markdown_generated_on == "Generated on"


@readable(
    intention="Si language_pack autogenera labels aceptados desde what_label y steps_label.",
    steps=[
        "Registra un idioma temporal usando language_pack con base en ingles",
        "Consulta el pack registrado",
        "Verifica labels aceptados autogenerados para what y steps",
    ],
    criteria=[
        "Los labels aceptados se autogeneran desde what_label y steps_label",
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
    intention="Si la compilacion de archivos po genera un archivo .mo valido.",
    steps=[
        "Crea un po temporal con una traduccion simple",
        "Ejecuta compile_po_file",
        "Verifica que el archivo .mo exista en disco",
    ],
    criteria=[
        "El archivo .mo se genera correctamente",
    ],
)
def test_compile_po_file_generates_mo_file(tmp_path):
    mo_path = _compile_sample_po(tmp_path)
    assert mo_path.exists()


@readable(
    intention="Si GNUTranslations puede cargar la traducción compilada desde el archivo .mo.",
    steps=[
        "Crea un po temporal con una traduccion simple",
        "Ejecuta compile_po_file y abre el mo con GNUTranslations",
        "Verifica que la clave traducida se resuelva al valor esperado",
    ],
    criteria=[
        "GNUTranslations puede leer la traduccion esperada",
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
    intention="Si parse_pytest_output extrae conteos y duración del resumen de pytest.",
    steps=[
        "Prepara una salida de pytest de ejemplo con casos PASSED, FAILED y SKIPPED",
        "Ejecuta parse_pytest_output",
        "Verifica cantidad recolectada, conteos del resumen y duración",
    ],
    criteria=[
        "El parser retorna conteos y duracion correctos",
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
    intention="Si parse_pytest_output identifica el nodeid fallido en los casos parseados.",
    steps=[
        "Prepara una salida de pytest de ejemplo con casos PASSED, FAILED y SKIPPED",
        "Ejecuta parse_pytest_output",
        "Verifica que el nodeid del caso FAILED quede identificado",
    ],
    criteria=[
        "El nodeid fallido queda identificado en la salida parseada",
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
    intention="Si render_natural_pytest_summary muestra encabezado y conteos en español.",
    steps=[
        "Construye un reporte parseado en memoria con un test pasado y uno fallido",
        "Ejecuta render_natural_pytest_summary con idioma es",
        "Verifica encabezado y conteos localizados",
    ],
    criteria=[
        "El reporte incluye encabezado y resumen de estado en español",
    ],
)
def test_render_natural_pytest_summary_localizes_header_and_counts():
    text = _render_sample_natural_summary_es()
    assert "Resumen natural de pytest" in text
    assert "Se recolectaron 2 tests." in text
    assert "1 pasaron, 1 fallaron." in text


@readable(
    intention="Si render_natural_pytest_summary incluye el nodeid fallido en el detalle final.",
    steps=[
        "Construye un reporte parseado en memoria con un test pasado y uno fallido",
        "Ejecuta render_natural_pytest_summary con idioma es",
        "Verifica presencia del nodeid fallido en el detalle final",
    ],
    criteria=[
        "Se lista el test fallido en el detalle final",
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
    intention="Si render_summary_text en español usa etiquetas de detalle localizadas.",
    steps=[
        "Construye una suite en memoria con un caso aprobado, descripcion y pasos",
        "Ejecuta render_summary_text con idioma español e inclusion de pasos",
        "Verifica encabezado, conteos y etiquetas localizadas",
    ],
    criteria=[
        "El resumen usa etiquetas de detalle en español",
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
    intention="Si render_summary_text en español muestra pasos, criterios y resumen final del caso.",
    steps=[
        "Construye una suite en memoria con un caso aprobado, descripcion y pasos",
        "Ejecuta render_summary_text con idioma español e inclusion de pasos",
        "Verifica pasos, criterios y resumen final del reporte",
    ],
    criteria=[
        "Se renderizan pasos y criterios del caso",
    ],
)
def test_render_summary_text_spanish_renders_steps_and_criteria():
    text = _render_spanish_detailed_summary()
    assert "1. Retorna estado aprobado" in text
    assert "Resumen final: total=1, aprobadas=1, fallidas=0, omitidas=0" in text


@readable(
    intention="Si render_summary_text conserva labels por idioma para casos en español e inglés.",
    steps=[
        "Construye una suite con un caso en español y otro en ingles",
        "Ejecuta render_summary_text en modo detallado",
        "Verifica labels de estado, intención y pasos por idioma",
    ],
    criteria=[
        "Cada caso conserva sus labels de idioma para estado, intención y pasos",
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
    intention="Si render_summary_text muestra placeholders localizados cuando faltan criterios.",
    steps=[
        "Construye una suite con un caso en español y otro en ingles sin criterios",
        "Ejecuta render_summary_text en modo detallado",
        "Verifica placeholders de criterios en español e inglés",
    ],
    criteria=[
        "Cuando faltan criterios se muestra placeholder localizado",
    ],
)
def test_render_summary_text_uses_localized_missing_criteria_placeholders():
    text = _render_mixed_language_summary()
    assert "Condiciones para aprobar:" in text
    assert "1. Sin criterios documentados" in text
    assert "Pass conditions:" in text
    assert "1. No pass conditions documented" in text


@readable(
    intention="Si parse_decorated_spec_file selecciona metadata en español para el idioma solicitado.",
    steps=[
        "Crea un archivo temporal con readable y campos title intention steps en ingles y español",
        "Ejecuta parse_decorated_spec_file con idioma español",
        "Verifica que el resultado use nombre e intención en español",
    ],
    criteria=[
        "parse_decorated_spec_file selecciona metadata en español",
    ],
)
def test_parse_decorated_spec_file_selects_spanish_metadata(tmp_path):
    parsed = _parse_i18n_decorated_spec(tmp_path)
    assert parsed["title"] == "test_sample.py"
    assert parsed["tests"][0]["name"] == "Maneja carga vacia"
    assert parsed["tests"][0]["what"] == "Regresa un error controlado"


@readable(
    intention="Si parse_decorated_spec_file preserva pasos y criterios i18n como listas.",
    steps=[
        "Crea un archivo temporal con readable y campos i18n para steps y criteria",
        "Ejecuta parse_decorated_spec_file con idioma español",
        "Verifica que los pasos y criterios queden preservados como listas",
    ],
    criteria=[
        "Los pasos y criterios se preservan como listas",
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
    intention="Si parse_decorated_spec_file extrae intention y título esperados desde @readable.",
    steps=[
        "Crea un archivo temporal con readable, intention y steps multilinea",
        "Ejecuta parse_decorated_spec_file en ingles",
        "Verifica título, nombre del caso e intención extraída",
    ],
    criteria=[
        "El intention y titulo se extraen con los valores esperados",
    ],
)
def test_parse_decorated_spec_file_extracts_intention_and_title(tmp_path):
    parsed = _parse_readable_multiline_steps_file(tmp_path)
    assert parsed["title"] == "test_sample.py"
    assert parsed["tests"][0]["name"] == "test_sample.py"
    assert parsed["tests"][0]["what"] == "Parses english fields"


@readable(
    intention="Si parse_decorated_spec_file normaliza steps multilinea numerados a lista ordenada.",
    steps=[
        "Crea un archivo temporal con readable, intention y steps multilinea",
        "Ejecuta parse_decorated_spec_file en ingles",
        "Verifica que los pasos se normalicen como lista ordenada",
    ],
    criteria=[
        "El parser normaliza pasos multilinea a lista ordenada",
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
    intention="Si el decorator readable conserva intention y title esperados en la metadata.",
    steps=[
        "Define un test decorado con readable usando intention y steps multilinea",
        "Lee __spec_meta__ de la funcion decorada",
        "Verifica que title e intention queden almacenados con valores esperados",
    ],
    criteria=[
        "La metadata almacenada conserva intention y title esperados",
    ],
)
def test_readable_decorator_preserves_intention_and_title():
    metadata = _build_readable_metadata_from_multiline_strings()
    assert metadata["title"] == "test_sample.py"
    assert metadata["intention"] == "Parses english fields"


@readable(
    intention="Si el decorator readable normaliza steps y criteria cuando se definen como texto multilinea.",
    steps=[
        "Define un test decorado con readable usando intention y steps/criteria en texto",
        "Lee __spec_meta__ de la funcion decorada",
        "Verifica que steps y criteria se normalicen a listas limpias",
    ],
    criteria=[
        "El decorator normaliza steps y criteria a listas limpias",
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
    intention="Si detect_language_from_decorators devuelve None cuando los idiomas empatan.",
    steps=[
        "Crea dos archivos de prueba, uno con metadata en ingles y otro en español",
        "Ejecuta detect_language_from_decorators sobre el directorio",
        "Verifica que retorna None porque los puntajes se empatan",
    ],
    criteria=[
        "El detector ignora cuando no hay predominio entre idiomas",
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
    intention="Si detect_language_from_decorators prioriza español cuando hay pistas en ese idioma.",
    steps=[
        "Crea un archivo con metadata que usa acentos y etiquetas españolas",
        "Ejecuta detect_language_from_decorators sobre el directorio",
        "Confirma que retorna 'es' porque los tokens españoles dominan",
    ],
    criteria=[
        "Las pistas lingüísticas hacen que se elija español en modo auto",
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
    intention="Ensures missing readable metadata is detected for module and class tests.",
    steps=[
        "Create test files with decorated and undecorated test functions",
        "Run find_tests_without_readable on the temporary directory",
        "Verify only undecorated tests are reported",
    ],
    criteria=[
        "The result contains exactly test functions without the readable decorator",
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
    intention="Ensures CLI missing-readable mode reports missing tests and skips pytest execution.",
    steps=[
        "Create a temporary test without @readable",
        "Intercept subprocess.run to prevent real pytest execution",
        "Run cli.main with --find-missing and validate output",
    ],
    criteria=[
        "CLI returns failure and lists missing tests without calling subprocess.run",
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
    intention="Si el wrapper readable elimina el token posicional pytest redundante del comando.",
    steps=[
        "Intercepta subprocess.run del CLI",
        "Ejecuta main con argumentos pytest y q",
        "Verifica que el comando final no incluya el token redundante",
    ],
    criteria=[
        "El comando final elimina token pytest redundante",
    ],
)
def test_cli_ignores_leading_pytest_token_in_forwarded_command(monkeypatch):
    code, captured = _run_cli_main_with_leading_pytest(monkeypatch)
    assert code == 0
    assert captured["command"] == ["pytest", "--readable", "-q", "--color=yes", "--readable-include-steps"]


@readable(
    intention="Si el wrapper readable activa flags de readable y opciones de captura esperadas.",
    steps=[
        "Intercepta subprocess.run del CLI",
        "Ejecuta main con argumentos pytest y q",
        "Verifica modo texto, captura de salida y check desactivado",
    ],
    criteria=[
        "Se activan flags de readable y opciones de captura esperadas",
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
    intention="Si readable pytest --lang=es reenvía el idioma al comando final.",
    steps=[
        "Intercepta subprocess.run del CLI",
        "Ejecuta main con argumentos pytest y lang es",
        "Verifica que el comando final incluya readable-lang=es",
    ],
    criteria=[
        "El comando final incluye readable-lang=es",
    ],
)
def test_cli_forwards_lang_to_pytest_command(monkeypatch):
    code, captured_command = _run_cli_main_with_lang_es(monkeypatch)
    assert code == 0
    assert "--readable-lang=es" in captured_command


@readable(
    intention="Si readable pytest --lang=es aplica defaults silenciosos y readable-include-steps.",
    steps=[
        "Intercepta subprocess.run del CLI",
        "Ejecuta main con argumentos pytest y lang es",
        "Verifica flags q, no-header, color y readable-include-steps",
    ],
    criteria=[
        "Se aplican defaults silenciosos y readable-include-steps",
    ],
)
def test_cli_forwards_lang_and_applies_quiet_defaults(monkeypatch):
    code, captured_command = _run_cli_main_with_lang_es(monkeypatch)
    assert code == 0
    assert captured_command == [
        "pytest",
        "--readable",
        "--readable-lang=es",
        "-q",
        "--no-header",
        "--color=yes",
        "--readable-include-steps",
    ]


def _run_cli_main_with_lang_es(monkeypatch):
    captured: dict[str, list[str]] = {}

    def fake_run(command: list[str], *, text: bool, capture_output: bool, check: bool) -> subprocess.CompletedProcess:
        captured["command"] = command
        return subprocess.CompletedProcess(command, 0, stdout="Resumen legible\n- Total: 0\n", stderr="")

    monkeypatch.setattr(cli.subprocess, "run", fake_run)

    code = cli.main(["pytest", "--lang=es"])
    return code, captured["command"]


@readable(
    intention="Si el wrapper readable conserva secciones relevantes de fallo al filtrar la salida.",
    steps=[
        "Simula salida con FAILURES, warnings, short summary y bloque readable",
        "Ejecuta el impresor filtrado del CLI",
        "Verifica inclusión de secciones relevantes en la salida renderizada",
    ],
    criteria=[
        "Se conservan secciones relevantes de fallo y bloque readable",
    ],
)
def test_cli_prints_relevant_sections_when_pytest_fails(capsys):
    rendered = _render_filtered_cli_failure_output(capsys)
    assert "FAILURES" in rendered
    assert "warnings summary" in rendered
    assert "short test summary info" in rendered
    assert "Resumen legible" in rendered


@readable(
    intention="Si el wrapper readable omite la línea final de resumen bruto de pytest al filtrar fallas.",
    steps=[
        "Simula salida con FAILURES, warnings, short summary y bloque readable",
        "Ejecuta el impresor filtrado del CLI",
        "Verifica que no se imprima la línea final de resumen bruto",
    ],
    criteria=[
        "No se imprime la linea final de resumen bruto de pytest",
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
