pytest_plugins = ["pytester"]

import csv
import pytest

from pytest_readable.decorators import readable
from pytest_readable.plugin import ReadableRuntimePlugin


@readable(
    intention="Si el plugin registra sus flags y aparecen en pytest help.",
    steps=[
        "Ejecuta pytest con help",
        "Busca flags readable en la salida",
        "Verifica que todas las opciones esperadas esten presentes",
    ],
    criteria=[
        "La salida de help incluye todas las flags readable esperadas",
    ],
)
def test_help_exposes_readable_options(pytester):
    result = pytester.runpytest("--help")

    result.stdout.fnmatch_lines(
        [
            "*--readable*",
            "*--readable-tree*",
            "*--readable-docs*",
            "*--readable-out=PATH*",
            "*--readable-format={markdown,csv}*",
            "*--readable-lang={auto,en,es}*",
            "*--export*",
        ]
    )


@readable(
    intention="Si readable muestra el encabezado y total en el resumen integrado.",
    steps=[
        "Crea un test simple en un proyecto temporal",
        "Ejecuta pytest con readable y readable-lang=en",
        "Verifica presencia del encabezado y total de pruebas en la salida",
    ],
    criteria=[
        "La salida contiene Readable summary y el total correcto",
    ],
)
def test_readable_prints_summary_header_and_total(pytester):
    result = _run_readable_summary(pytester)
    result.stdout.fnmatch_lines(["*Readable summary*", "*- Total: 1*"])


@readable(
    intention="Si readable mantiene outcomes de pytest al ejecutar una prueba aprobada.",
    steps=[
        "Crea un test simple en un proyecto temporal",
        "Ejecuta pytest con readable y readable-lang=en",
        "Verifica que pytest reporte exactamente un test aprobado",
    ],
    criteria=[
        "Pytest reporta el test como aprobado",
    ],
)
def test_readable_prints_summary_reports_passed_outcome(pytester):
    result = _run_readable_summary(pytester)
    result.assert_outcomes(passed=1)


def _run_readable_summary(pytester):
    pytester.makepyfile(
        test_sample="""
        def test_ok():
            assert True
        """
    )

    return pytester.runpytest("--readable", "--readable-lang=en", "-q")


@readable(
    intention="Si collect-only con readable-tree imprime jerarquia por modulo y clase.",
    steps=[
        "Crea un test dentro de una clase",
        "Ejecuta pytest en collect-only con readable-tree",
        "Verifica modulo, clase y nombre legible",
    ],
    criteria=[
        "El arbol incluye modulo, clase y nombre de prueba normalizado",
    ],
)
def test_collect_only_readable_tree_prints_hierarchy(pytester):
    pytester.makepyfile(
        test_pipeline="""
        class TestPipeline:
            def test_embedding_step(self):
                assert True
        """
    )

    result = pytester.runpytest("--collect-only", "--readable-tree", "-q")

    result.stdout.fnmatch_lines(["*test_pipeline.py*", "*TestPipeline*", "*embedding step*"])


@readable(
    intention="Si readable con intention y pasos multilinea aparece en la salida detallada.",
    steps=[
        "Crea un test temporal con readable intention y steps multilinea",
        "Ejecuta pytest en collect-only con readable include-steps",
        "Verifica encabezado, detalle e impresion de pasos",
    ],
    criteria=[
        "La salida incluye intention, pasos y criterios documentados del caso temporal",
    ],
)
def test_readable_decorator_with_multiline_steps_is_rendered(pytester):
    pytester.makepyfile(
        test_sample='''
        from pytest_readable.decorators import readable

        @readable(
            title="test_sample.py",
            intention="Parses english fields",
            steps="""
        1. Read the file
        2. Extract the fields
        """,
            criteria="""
        1. Returns expected fields
        2. Keeps order stable
        """,
        )
        def test_parse_spec_file_accepts_english_labels(tmp_path):
            assert tmp_path is not None
        '''
    )

    result = pytester.runpytest(
        "--collect-only",
        "--readable",
        "--readable-lang=en",
        "--readable-include-steps",
        "-q",
    )

    stdout = result.stdout.str()
    assert "Readable summary" in stdout
    assert "- [collected] test_sample.py::test_parse_spec_file_accepts_english_labels" in stdout
    assert "What it tests: Parses english fields" in stdout
    assert "1. Read the file" in stdout
    assert "2. Extract the fields" in stdout
    assert "Pass conditions:" in stdout
    assert "1. Returns expected fields" in stdout
    assert "2. Keeps order stable" in stdout


@readable(
    intention="Si el plugin crea el archivo markdown cuando se exporta documentación.",
    steps=[
        "Crea un test temporal",
        "Ejecuta pytest en collect-only con formato markdown y ruta de salida",
        "Verifica que el archivo markdown exista en la ruta de salida",
    ],
    criteria=[
        "Se crea el archivo markdown en la ruta indicada",
    ],
)
def test_plugin_exports_markdown_creates_output_file(pytester):
    result, out_file, _ = _export_markdown_docs(pytester)
    assert out_file.exists()
    result.stdout.fnmatch_lines(["*readable docs exported:*tests-readable.md*"])


@readable(
    intention="Si el markdown exportado contiene encabezado y detalle esperado del caso.",
    steps=[
        "Crea un test temporal",
        "Ejecuta pytest en collect-only con formato markdown y ruta de salida",
        "Verifica encabezado y campos esperados en el contenido exportado",
    ],
    criteria=[
        "El contenido exportado contiene el encabezado esperado",
    ],
)
def test_plugin_exports_markdown_includes_expected_content(pytester):
    _, _, rendered = _export_markdown_docs(pytester)
    assert "# Test Specs" in rendered
    assert "- nodeid: `test_docs.py::test_documented_case`" in rendered
    assert "- status: `collected`" in rendered


@readable(
    intention="Si --export=markdown habilita la exportación directamente desde el flag nuevo.",
    steps=[
        "Crea un test temporal",
        "Ejecuta pytest collect-only con --readable y --export=markdown",
        "Confirma que el archivo Markdown se crea y el log reporta la exportación",
    ],
    criteria=[
        "La exportación ocurre usando solo el flag --export",
    ],
)
def test_plugin_exports_markdown_with_export_flag(pytester):
    result, out_file, _ = _run_export_docs(pytester, "markdown", via_export_flag=True)
    assert out_file.exists()
    result.stdout.fnmatch_lines(["*readable docs exported:*tests-readable.md*"])


@readable(
    intention="Si --export=csv crea exportación CSV idéntica a --readable-docs.",
    steps=[
        "Crea un test temporal",
        "Ejecuta pytest collect-only con --readable y --export=csv",
        "Confirma que el archivo CSV se genera y se reporta la exportación",
    ],
    criteria=[
        "La exportación CSV funciona cuando se usa el flag --export",
    ],
)
def test_plugin_exports_csv_with_export_flag(pytester):
    result, out_file, _ = _run_export_docs(pytester, "csv", via_export_flag=True)
    assert out_file.exists()
    result.stdout.fnmatch_lines(["*readable docs exported:*tests-readable.csv*"])


@readable(
    intention="Si la exportación se ejecuta aunque exista una prueba fallida.",
    steps=[
        "Crea un test temporal que falla",
        "Ejecuta pytest con --readable y --export=markdown",
        "Verifica que el archivo de salida se haya creado",
    ],
    criteria=[
        "El archivo markdown se exporta incluso cuando pytest termina con fallo",
    ],
)
def test_plugin_exports_markdown_even_when_tests_fail(pytester):
    result, out_file = _run_export_docs_with_failure(pytester, "markdown")
    assert out_file.exists()
    result.assert_outcomes(failed=1)
    result.stdout.fnmatch_lines(["*readable docs exported:*tests-readable.md*"])


def _export_markdown_docs(pytester):
    return _run_export_docs(pytester, "markdown")


@readable(
    intention="Si el plugin crea el archivo CSV en la ruta indicada.",
    steps=[
        "Crea un test temporal",
        "Ejecuta pytest en collect-only con formato csv y ruta de salida",
        "Verifica que el archivo CSV exista en la ruta de salida",
    ],
    criteria=[
        "Se crea el archivo CSV en la ruta indicada",
    ],
)
def test_plugin_exports_csv_creates_output_file(pytester):
    _, out_file, _ = _export_csv_docs(pytester)
    assert out_file.exists()


@readable(
    intention="Si el CSV exportado incluye encabezados y columnas esperadas para el caso.",
    steps=[
        "Crea un test temporal",
        "Ejecuta pytest en collect-only con formato csv y ruta de salida",
        "Verifica encabezados y valores clave de la fila exportada",
    ],
    criteria=[
        "La cabecera CSV coincide con las columnas esperadas",
    ],
)
def test_plugin_exports_csv_includes_expected_columns(pytester):
    _, out_file, _ = _export_csv_docs(pytester)
    assert out_file.exists()
    csv_lines = out_file.read_text(encoding="utf-8").splitlines()
    reader = csv.reader(csv_lines)
    headers = next(reader)
    row = next(reader)
    assert headers[:4] == ["File", "Class", "Test", "What it tests"]
    assert row[0].endswith("test_docs.py")
    assert row[2] == "documented case"
    assert row[5] == "collected"
    assert row[6] == "test_docs.py::test_documented_case"


def _export_csv_docs(pytester):
    return _run_export_docs(pytester, "csv")


def _run_export_docs(pytester, format_: str, *, via_export_flag: bool = False):
    pytester.makepyfile(
        test_docs="""
        def test_documented_case():
            assert True
        """
    )
    extension = "md" if format_ == "markdown" else "csv"
    out_file = pytester.path / "docs" / f"tests-readable.{extension}"

    args = [
        "--collect-only",
        "--readable",
        "--readable-lang=en",
    ]
    if via_export_flag:
        args.append(f"--export={format_}")
    else:
        args.extend(["--readable-docs", f"--readable-format={format_}"])
    args.append(f"--readable-out={out_file}")
    args.append("-q")

    result = pytester.runpytest(*args)
    rendered = out_file.read_text(encoding="utf-8") if out_file.exists() else ""
    return result, out_file, rendered


def _run_export_docs_with_failure(pytester, format_: str):
    pytester.makepyfile(
        test_docs="""
        def test_failing_case():
            assert False
        """
    )
    extension = "md" if format_ == "markdown" else "csv"
    out_file = pytester.path / "docs" / f"tests-readable.{extension}"

    result = pytester.runpytest(
        "--readable",
        "--readable-lang=en",
        f"--export={format_}",
        f"--readable-out={out_file}",
        "-q",
    )
    return result, out_file


@readable(
    intention_en="Ensures --readable-lang=es renders the summary header in Spanish.",
    steps_en=[
        "Create a temporary test",
        "Run pytest collect-only with readable output and Spanish language",
        "Verify that 'Resumen legible' appears",
    ],
    criteria_en=[
        "The summary header is rendered in Spanish",
    ],
)
@pytest.mark.es_lang_only
def test_plugin_honors_readable_lang_es(pytester):
    pytester.makepyfile(
        test_lang="""
        def test_ok():
            assert True
        """
    )

    result = pytester.runpytest(
        "--collect-only",
        "--readable",
        "--readable-lang=es",
        "-q",
    )

    result.stdout.fnmatch_lines(["*Resumen legible*"])


@readable(
    intention="Ensures --readable-lang=en keeps the readable summary header in English.",
    steps=[
        "Crea un test temporal",
        "Ejecuta pytest collect-only con readable y lenguaje inglés",
        "Verifica que aparezca 'Readable summary'",
    ],
    criteria=[
        "El encabezado del resumen se renderiza en inglés",
    ],
)
@pytest.mark.en_lang_only
def test_plugin_honors_readable_lang_en(pytester):
    pytester.makepyfile(
        test_lang="""
        def test_ok():
            assert True
        """
    )

    result = pytester.runpytest(
        "--collect-only",
        "--readable",
        "--readable-lang=en",
        "-q",
    )

    result.stdout.fnmatch_lines(["*Readable summary*"])


@readable(
    intention_es="Verifica que --readable-lang=auto prioriza metadata del decorator sobre el entorno forzado.",
    steps_es=[
        "Fuerza las variables de entorno a inglés",
        "Crea un test con metadata del decorator en español",
        "Ejecuta pytest collect-only con --readable-lang=auto",
        "Confirma que el encabezado del resumen se renderiza en español",
    ],
    criteria_es=[
        "La detección auto prefiere la metadata en español por encima de las variables del entorno",
    ],
)
@pytest.mark.auto_lang_only
def test_plugin_auto_lang_detects_from_decorators_es(pytester, monkeypatch):
    monkeypatch.setenv("PYTEST_READABLE_LANG", "en_US.UTF-8")
    monkeypatch.setenv("LC_ALL", "en_US.UTF-8")
    monkeypatch.setenv("LANG", "en_US.UTF-8")
    pytester.makepyfile(
        test_auto_lang='''
        from pytest_readable.decorators import readable

        @readable(
            intention="Si detecta idioma español desde decorators",
            steps=["Define metadata en español", "Renderiza en modo auto"],
        )
        def test_detects_es():
            assert True
        '''
    )

    result = pytester.runpytest("--collect-only", "--readable", "--readable-lang=auto", "-q")
    result.stdout.fnmatch_lines(["*Resumen legible*"])


@readable(
    intention_en="Ensures auto language picks decorator metadata instead of forced environment.",
    steps_en=[
        "Set environment variables to Spanish",
        "Create a test whose decorator metadata is written in English",
        "Run pytest collect-only with --readable-lang=auto",
        "Confirm the summary header renders in English",
    ],
    criteria_en=[
        "Auto detection prefers decorator metadata in English over the spicy env settings",
    ],
)
@pytest.mark.auto_lang_only
def test_plugin_auto_lang_detects_from_decorators_en(pytester, monkeypatch):
    monkeypatch.setenv("PYTEST_READABLE_LANG", "es_MX.UTF-8")
    monkeypatch.setenv("LC_ALL", "es_MX.UTF-8")
    monkeypatch.setenv("LANG", "es_MX.UTF-8")
    pytester.makepyfile(
        test_auto_lang_en='''
        from pytest_readable.decorators import readable

        @readable(
            intention="Validates English metadata despite Spanish environment",
            steps=["Create English metadata"],
            criteria=["Reports English header"],
        )
        def test_detects_en():
            assert True
        '''
    )

    result = pytester.runpytest("--collect-only", "--readable", "--readable-lang=auto", "-q")
    result.stdout.fnmatch_lines(["*Readable summary*"])


@readable(
    intention="Si un test no tiene metadata readable, el arbol usa el nombre normalizado de la funcion.",
    steps=[
        "Crea un test sin metadata decorada",
        "Ejecuta collect-only con arbol readable",
        "Verifica que el arbol imprima el nombre derivado de la funcion",
    ],
    criteria=[
        "El arbol usa el nombre de funcion normalizado cuando no hay metadata",
    ],
)
def test_plugin_tree_without_readable_uses_function_name(pytester):
    pytester.makepyfile(
        test_query="""
        def test_blackboard_pipeline():
            assert True
        """
    )

    result = pytester.runpytest(
        "--collect-only",
        "--readable-tree",
        "--readable-lang=es",
        "-q",
    )

    result.stdout.fnmatch_lines(["*blackboard pipeline*"])


@readable(
    intention="Si el resumen detallado en auto conserva labels y estado del caso en español.",
    steps=[
        "Crea dos pruebas temporales con readable, una en español y otra en ingles",
        "Ejecuta pytest collect-only con readable-lang=auto e include-steps",
        "Verifica que el caso en español use sus labels y estado en español",
    ],
    criteria=[
        "El caso en español usa labels y estado en español",
    ],
)
@pytest.mark.auto_lang_only
def test_plugin_applies_case_language_strategy_in_detailed_list_es(pytester):
    stdout = _run_case_language_strategy(pytester)
    assert "- [recolectadas] test_lang.py::test_case_es" in stdout
    assert "Qué prueba: Valida comportamiento en español" in stdout
    assert "Pasos:" in stdout


@readable(
    intention_en="Ensures auto detailed summary keeps labels and status for the English case.",
    steps_en=[
        "Create two temporary tests with readable metadata in Spanish and English",
        "Run pytest collect-only with readable-lang=auto and include-steps",
        "Verify that the English case uses labels and status in English",
    ],
    criteria_en=[
        "The English case uses labels and status in English",
    ],
)
@pytest.mark.auto_lang_only
def test_plugin_applies_case_language_strategy_in_detailed_list_en(pytester):
    stdout = _run_case_language_strategy(pytester)
    assert "- [collected] test_lang.py::test_case_en" in stdout
    assert "What it tests: Validates behavior in English" in stdout
    assert "Steps:" in stdout


@pytest.mark.auto_lang_only
def _run_case_language_strategy(pytester):
    pytester.makepyfile(
        test_lang='''
        from pytest_readable.decorators import readable

        @readable(
            intention_es="Valida comportamiento en español",
            steps_es=["Ejecuta caso español"],
        )
        def test_case_es():
            assert True

        @readable(
            intention_en="Validates behavior in English",
            steps_en=["Run English case"],
        )
        def test_case_en():
            assert True
        '''
    )

    result = pytester.runpytest(
        "--collect-only",
        "--readable",
        "--readable-lang=auto",
        "--readable-include-steps",
        "-q",
    )

    return result.stdout.str()


@readable(
    intention="Si readable-lang=en fuerza etiquetas y metadata en inglés aunque el decorator tenga contenido en español.",
    steps=[
        "Crea un test temporal con metadata readable en español",
        "Ejecuta pytest collect-only con readable-lang=en e include-steps",
        "Verifica que status, etiquetas y contenido se rendericen en inglés",
    ],
    criteria=[
        "La salida usa etiquetas y contenido en inglés a pesar de que la metadata original está en español",
    ],
)
def test_plugin_forced_lang_overrides_case_detection(pytester):
    pytester.makepyfile(
        test_lang='''
        from pytest_readable.decorators import readable

        @readable(
            intention_es="Valida comportamiento en español",
            intention_en="Validates behavior in English",
            steps_es=["Ejecuta caso español"],
            steps_en=["Run English case"],
            criteria_es=["Retorna estado esperado"],
            criteria_en=["Returns expected status"],
        )
        def test_case_es():
            assert True
        '''
    )

    result = pytester.runpytest(
        "--collect-only",
        "--readable",
        "--readable-lang=en",
        "--readable-include-steps",
        "-q",
    )

    stdout = result.stdout.str()
    assert "- [collected] test_lang.py::test_case_es" in stdout
    assert "What it tests: Validates behavior in English" in stdout
    assert "Steps:" in stdout
    assert "1. Run English case" in stdout
    assert "Pass conditions:" in stdout
    assert "1. Returns expected status" in stdout


@readable(
    intention="Si readable-lang=es fuerza etiquetas y metadata en español aunque el decorator tenga contenido en inglés.",
    steps=[
        "Crea un test temporal con metadata readable en inglés",
        "Ejecuta pytest collect-only con readable-lang=es e include-steps",
        "Verifica que status, etiquetas y contenido se rendericen en español",
    ],
    criteria=[
        "La salida usa etiquetas y contenido en español aunque la metadata original esté en inglés",
    ],
)
def test_plugin_forced_lang_overrides_case_detection_es(pytester):
    pytester.makepyfile(
        test_lang='''
        from pytest_readable.decorators import readable

        @readable(
            intention_es="Valida comportamiento en español",
            intention_en="Validates behavior in English",
            steps_es=["Ejecuta caso español"],
            steps_en=["Run English case"],
            criteria_es=["Retorna estado esperado"],
            criteria_en=["Returns expected status"],
        )
        def test_case_en():
            assert True
        '''
    )

    result = pytester.runpytest(
        "--collect-only",
        "--readable",
        "--readable-lang=es",
        "--readable-include-steps",
        "-q",
    )

    stdout = result.stdout.str()
    assert "- [recolectadas] test_lang.py::test_case_en" in stdout
    assert "Qué prueba: Valida comportamiento en español" in stdout
    assert "Pasos:" in stdout
    assert "1. Ejecuta caso español" in stdout
    assert "Condiciones para aprobar:" in stdout
    assert "1. Retorna estado esperado" in stdout


@readable(
    intention="Si el plugin aplica color amarillo a lineas de intencion en ambos idiomas.",
    steps=[
        "Crea instancia del plugin runtime",
        "Evalua estilo para linea en español y linea en ingles",
        "Verifica que ambas devuelvan color amarillo",
    ],
    criteria=[
        "Si \"Qué prueba\" está pintada de color amarillo en salida ANSI",
    ],
)
def test_plugin_styles_intention_lines_in_yellow():
    plugin = ReadableRuntimePlugin(config=None)

    assert plugin._line_style("    Qué prueba: valida algo") == {"yellow": True}
    assert plugin._line_style("    What it tests: validates something") == {"yellow": True}
    assert plugin._line_style("    Condiciones para aprobar:") == {"blue": True}
    assert plugin._line_style("    Pass conditions:") == {"blue": True}


@readable(
    intention="Si el reporte de plugin pinta en azul el encabezado de criterios en salida ANSI.",
    steps=[
        "Crea un test temporal con metadata de criterios",
        "Ejecuta pytest collect-only con readable y color forzado",
        "Verifica que la linea de criterios salga con codigo ANSI azul",
    ],
    criteria=[
        "La salida contiene \"Condiciones para aprobar\" con secuencia ANSI de color azul",
    ],
)
def test_plugin_reports_criteria_header_in_blue(pytester):
    pytester.makepyfile(
        test_color='''
        from pytest_readable.decorators import readable

        @readable(
            intention="Valida color de criterios",
            steps=["Ejecuta reporte legible"],
            criteria=["Renderiza encabezado azul"],
        )
        def test_color_case():
            assert True
        '''
    )

    result = pytester.runpytest(
        "--collect-only",
        "--readable",
        "--readable-lang=es",
        "--readable-include-steps",
        "--color=yes",
        "-q",
    )

    stdout = result.stdout.str()
    assert "Condiciones para aprobar:" in stdout
    assert "\x1b[34m" in stdout
