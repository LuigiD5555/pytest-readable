import subprocess
from gettext import GNUTranslations
from pathlib import Path

import pytest_readable.cli as cli
from pytest_readable.compile_locales import compile_po_file
from pytest_readable.core.exporters import render_csv
from pytest_readable.core.models import ReadableSuite, ReadableTestCase
from pytest_readable.core.parser import (
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
    intent="Si la exportacion markdown usa encabezados y labels traducidos al idioma seleccionado.",
    steps=[
        "Construye una suite en memoria con un caso documentado",
        "Ejecuta render_markdown con idioma español",
        "Verifica presencia de titulo, marca de fecha y labels traducidos",
    ],
)
def test_markdown_export_localizes_title_and_labels():
    suite = ReadableSuite(
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

    markdown = render_markdown(suite, "es")

    assert "# Especificaciones de tests" in markdown
    assert "_Generado el " in markdown
    assert "**Si prueba:** Retorna documentos ordenados" in markdown
    assert "**Pasos:**" in markdown


@readable(
    intent="Si la exportacion csv genera encabezados traducidos al idioma seleccionado.",
    steps=[
        "Construye una suite en memoria",
        "Ejecuta render_csv con idioma español",
        "Verifica que el encabezado inicia con columnas esperadas en español",
    ],
)
def test_csv_export_localizes_headers():
    suite = ReadableSuite(
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

    csv_content = render_csv(suite, "es")

    assert csv_content.startswith("Archivo,Clase,Test,Si prueba,Pasos,Estado,NodeID")


@readable(
    intent="Si la resolucion de idioma usa el argumento explicito por encima de variables de entorno.",
    steps=[
        "Define PYTEST_READABLE_LANG con valor español",
        "Llama resolve_language con argumento en",
        "Verifica que el resultado final sea ingles",
    ],
)
def test_resolve_language_prefers_explicit_argument(monkeypatch):
    monkeypatch.setenv("PYTEST_READABLE_LANG", "es_MX.UTF-8")

    assert resolve_language("en") == "en"


@readable(
    intent="Si en modo auto se usa el idioma del entorno.",
    steps=[
        "Define LANG con una localidad en español",
        "Llama resolve_language en auto",
        "Verifica que el idioma resultante sea español",
    ],
)
def test_resolve_language_uses_environment_when_auto(monkeypatch):
    monkeypatch.delenv("PYTEST_READABLE_LANG", raising=False)
    monkeypatch.delenv("LC_ALL", raising=False)
    monkeypatch.setenv("LANG", "es_MX.UTF-8")

    assert resolve_language("auto") == "es"


@readable(
    intent="Si la resolucion de idioma vuelve a ingles cuando no hay argumento ni variables de entorno.",
    steps=[
        "Limpia PYTEST_READABLE_LANG, LC_ALL y LANG",
        "Llama resolve_language sin argumentos",
        "Verifica que el resultado sea en",
    ],
)
def test_resolve_language_defaults_to_english(monkeypatch):
    monkeypatch.delenv("PYTEST_READABLE_LANG", raising=False)
    monkeypatch.delenv("LC_ALL", raising=False)
    monkeypatch.delenv("LANG", raising=False)

    assert resolve_language() == "en"


@readable(
    intent="Si get_i18n obtiene traducciones reales desde los catalogos compilados.",
    steps=[
        "Solicita instancia i18n en español",
        "Consulta una clave traducible conocida",
        "Verifica que el texto retornado sea la traduccion esperada",
    ],
)
def test_get_i18n_uses_gettext_catalogs():
    i18n = get_i18n("es")

    assert i18n.t("app_description") == "Visor interactivo de specs para pytest"


@readable(
    intent="Si el decorador language_pack registra un idioma nuevo heredando campos base y autocompleta labels aceptados.",
    steps=[
        "Registra un idioma temporal usando language_pack con base en ingles",
        "Consulta el pack registrado",
        "Verifica herencia de campos y labels aceptados autogenerados",
    ],
)
def test_language_pack_decorator_registers_with_base_defaults():
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

    assert pack.summary_title == "Resumo legivel"
    assert pack.list_title == "Lista detalhada"
    assert pack.markdown_title == "Especificacoes de teste"
    assert pack.markdown_generated_on == "Generated on"
    assert pack.accepted_what_labels == ("**O que testa:**", "**O que testa**:")
    assert pack.accepted_steps_labels == ("**Passos:**", "**Passos**:")


@readable(
    intent="Si la compilacion de archivos po genera un mo valido y legible.",
    steps=[
        "Crea un po temporal con una traduccion simple",
        "Ejecuta compile_po_file",
        "Abre el mo resultante con GNUTranslations",
        "Verifica que la clave traducida se resuelve al valor esperado",
    ],
)
def test_compile_po_file_generates_a_loadable_mo_catalog(tmp_path):
    po_content = """msgid ""
msgstr ""
"Language: es\\n"

msgid "app_description"
msgstr "Descripcion de prueba"
"""
    po_path = tmp_path / "pytest_readable.po"
    po_path.write_text(po_content, encoding="utf-8")

    mo_path = compile_po_file(po_path)

    assert mo_path.exists()
    with mo_path.open("rb") as fh:
        translations = GNUTranslations(fh)
    assert translations.gettext("app_description") == "Descripcion de prueba"


@readable(
    intent="Si el parser de salida de pytest identifica tests recolectados, resumen de estados, duracion y casos fallidos.",
    steps=[
        "Prepara una salida de pytest de ejemplo con casos PASSED, FAILED y SKIPPED",
        "Ejecuta parse_pytest_output",
        "Verifica cantidad recolectada, conteos del resumen, duracion y nodeid fallido",
    ],
)
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


@readable(
    intent="Si el renderizador genera un reporte legible en español con estado general y detalle de fallas.",
    steps=[
        "Construye un reporte parseado en memoria con un test pasado y uno fallido",
        "Ejecuta render_natural_pytest_summary con idioma es",
        "Verifica encabezado, conteos y presencia del nodeid fallido",
    ],
)
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


@readable(
    intent="Si el resumen detallado en español no mezcla etiquetas en ingles y muestra secciones claras.",
    steps=[
        "Construye una suite en memoria con un caso aprobado, descripcion y pasos",
        "Ejecuta render_summary_text con idioma español e inclusion de pasos",
        "Verifica encabezado, conteos localizados y etiquetas Si prueba y Pasos",
    ],
)
def test_render_summary_text_spanish_is_fully_localized():
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

    text = render_summary_text(suite, "es", include_steps=True)

    assert "Resumen legible" in text
    assert "- aprobadas: 1" in text
    assert "Lista detallada" in text
    assert "[aprobadas] tests/test_demo.py::test_ok" in text
    assert "Qué prueba: Valida caso correcto" in text
    assert "Pasos:" in text
    assert "Condiciones para aprobar:" in text
    assert "1. Retorna estado aprobado" in text
    assert "Resumen final: total=1, aprobadas=1, fallidas=0, omitidas=0" in text


@readable(
    intent="Si el resumen detallado puede mostrar labels por prueba cuando hay metadata en ingles y español.",
    steps=[
        "Construye una suite con un caso en español y otro en ingles",
        "Ejecuta render_summary_text en modo detallado",
        "Verifica que cada caso conserve sus labels de idioma",
    ],
)
def test_render_summary_text_uses_case_language_strategy():
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

    text = render_summary_text(suite, "es", include_steps=True)

    assert "Resumen legible" in text
    assert "[aprobadas] tests/test_demo.py::test_es" in text
    assert "[passed] tests/test_demo.py::test_en" in text
    assert "Qué prueba: Valida salida" in text
    assert "Pasos:" in text
    assert "What it tests: Validates output" in text
    assert "Steps:" in text


@readable(
    intent="Si el parser de decorators extrae titulo, descripcion y pasos del idioma solicitado.",
    steps=[
        "Crea un archivo temporal con readable y campos title intent steps en ingles y español",
        "Ejecuta parse_decorated_spec_file con idioma español",
        "Verifica que el resultado use textos españoles y preserve pasos",
    ],
)
def test_parse_decorated_spec_file_reads_i18n_metadata(tmp_path):
    test_file = tmp_path / "test_sample.py"
    test_file.write_text(
        """from pytest_readable.decorators import readable

@readable(
    title_en="Handles empty payload",
    title_es="Maneja carga vacia",
    intent_en="Returns a controlled error",
    intent_es="Regresa un error controlado",
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

    parsed = parse_decorated_spec_file(test_file, "es")

    assert parsed["title"] == "test_sample.py"
    assert parsed["tests"][0]["name"] == "Maneja carga vacia"
    assert parsed["tests"][0]["what"] == "Regresa un error controlado"
    assert parsed["tests"][0]["steps"] == ["Enviar carga vacia", "Validar ValueError"]
    assert parsed["tests"][0]["criteria"] == ["Lanza ValueError", "Registra el error"]


@readable(
    intent="Si el parser de decorators entiende readable, mapea intent y convierte pasos numerados en texto a lista.",
    steps=[
        "Crea un archivo temporal con readable, intent y steps multilinea",
        "Ejecuta parse_decorated_spec_file en ingles",
        "Verifica titulo, nombre del caso, intencion y pasos normalizados",
    ],
)
def test_parse_decorated_spec_file_accepts_readable_intent_and_multiline_steps(tmp_path):
    test_file = tmp_path / "test_sample.py"
    test_file.write_text(
        '''from pytest_readable.decorators import readable

@readable(
    title="test_sample.py",
    intent="Parses english fields",
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

    parsed = parse_decorated_spec_file(test_file, "en")

    assert parsed["title"] == "test_sample.py"
    assert parsed["tests"][0]["name"] == "test_sample.py"
    assert parsed["tests"][0]["what"] == "Parses english fields"
    assert parsed["tests"][0]["steps"] == ["Read the file", "Extract the fields"]


@readable(
    intent="Si el decorator readable guarda metadata homogenea intent y lista de pasos cuando steps llega en texto.",
    steps=[
        "Define un test decorado con readable usando intent y steps multilinea",
        "Lee __spec_meta__ de la funcion decorada",
        "Verifica titulo, campo intent y pasos como lista limpia",
    ],
)
def test_readable_decorator_normalizes_intent_and_text_steps():
    @readable(
        title="test_sample.py",
        intent="Parses english fields",
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

    metadata = test_parse_readable_metadata_accepts_english_labels.__spec_meta__

    assert metadata["title"] == "test_sample.py"
    assert metadata["intent"] == "Parses english fields"
    assert metadata["steps"] == ["Read the file", "Extract the fields"]
    assert metadata["criteria"] == ["Returns expected fields", "No parsing errors"]


@readable(
    intent="Si readable pytest elimina el token posicional pytest y lo reenvia correctamente.",
    steps=[
        "Intercepta subprocess.run del CLI",
        "Ejecuta main con argumentos pytest y q",
        "Verifica comando final y modo de captura",
    ],
)
def test_cli_ignores_leading_pytest_token(monkeypatch):
    captured: dict[str, list[str] | bool | str] = {}

    def fake_run(command: list[str], *, text: bool, capture_output: bool, check: bool) -> subprocess.CompletedProcess:
        captured["command"] = command
        captured["text"] = text
        captured["capture_output"] = capture_output
        captured["check"] = check
        return subprocess.CompletedProcess(command, 0, stdout="Resumen legible\n- Total: 0\n", stderr="")

    monkeypatch.setattr(cli.subprocess, "run", fake_run)

    code = cli.main(["pytest", "-q"])

    assert code == 0
    assert captured["command"] == ["pytest", "--readable", "-q", "--color=yes", "--readable-include-steps"]
    assert captured["text"] is True
    assert captured["capture_output"] is True
    assert captured["check"] is False


@readable(
    intent="Si readable pytest --lang=es transmite idioma y aplica salida silenciosa por defecto.",
    steps=[
        "Intercepta subprocess.run del CLI",
        "Ejecuta main con argumentos pytest y lang es",
        "Verifica flags readable-lang, q, no-header, color y readable-include-steps",
    ],
)
def test_cli_forwards_lang_and_uses_quiet_defaults(monkeypatch):
    captured: dict[str, list[str]] = {}

    def fake_run(command: list[str], *, text: bool, capture_output: bool, check: bool) -> subprocess.CompletedProcess:
        captured["command"] = command
        return subprocess.CompletedProcess(command, 0, stdout="Resumen legible\n- Total: 0\n", stderr="")

    monkeypatch.setattr(cli.subprocess, "run", fake_run)

    code = cli.main(["pytest", "--lang=es"])

    assert code == 0
    assert captured["command"] == [
        "pytest",
        "--readable",
        "--readable-lang=es",
        "-q",
        "--no-header",
        "--color=yes",
        "--readable-include-steps",
    ]


@readable(
    intent="Si el wrapper readable imprime solo secciones relevantes cuando pytest falla.",
    steps=[
        "Simula salida con FAILURES, warnings, short summary y bloque readable",
        "Ejecuta el impresor filtrado del CLI",
        "Verifica inclusion de secciones relevantes y exclusion del resumen final de pytest",
    ],
)
def test_cli_prints_only_relevant_sections_when_pytest_fails(capsys):
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
    rendered = capsys.readouterr().out

    assert "FAILURES" in rendered
    assert "warnings summary" in rendered
    assert "short test summary info" in rendered
    assert "Resumen legible" in rendered
    assert "1 failed in 0.01s" not in rendered
