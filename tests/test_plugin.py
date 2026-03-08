pytest_plugins = ["pytester"]


from pytest_readable.decorators import readable
from pytest_readable.plugin import ReadableRuntimePlugin


@readable(
    intent="Si el plugin registra sus flags y aparecen en pytest help.",
    steps=[
        "Ejecuta pytest con help",
        "Busca flags readable en la salida",
        "Verifica que todas las opciones esperadas esten presentes",
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
        ]
    )


@readable(
    intent="Si readable muestra un resumen integrado en el flujo de pytest.",
    steps=[
        "Crea un test simple en un proyecto temporal",
        "Ejecuta pytest con readable y readable-lang=en",
        "Verifica presencia del encabezado y total de pruebas",
    ],
)
def test_readable_prints_summary(pytester):
    pytester.makepyfile(
        test_sample="""
        def test_ok():
            assert True
        """
    )

    result = pytester.runpytest("--readable", "--readable-lang=en", "-q")

    result.stdout.fnmatch_lines(["*Readable summary*", "*- Total: 1*"])
    result.assert_outcomes(passed=1)


@readable(
    intent="Si collect-only con readable-tree imprime jerarquia por modulo y clase.",
    steps=[
        "Crea un test dentro de una clase",
        "Ejecuta pytest en collect-only con readable-tree",
        "Verifica modulo, clase y nombre legible",
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
    intent="Si readable con intent y pasos multilinea aparece en la salida detallada.",
    steps=[
        "Crea un test temporal con readable intent y steps multilinea",
        "Ejecuta pytest en collect-only con readable include-steps",
        "Verifica encabezado, detalle e impresion de pasos",
    ],
)
def test_readable_decorator_with_multiline_steps_is_rendered(pytester):
    pytester.makepyfile(
        test_sample='''
        from pytest_readable.decorators import readable

        @readable(
            title="test_sample.py",
            intent="Parses english fields",
            steps="""
        1. Read the file
        2. Extract the fields
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


@readable(
    intent="Si el plugin puede exportar documentacion markdown con readable-docs.",
    steps=[
        "Crea un test temporal",
        "Ejecuta pytest en collect-only con formato markdown y ruta de salida",
        "Verifica que el archivo se genere con encabezado correcto",
    ],
)
def test_plugin_exports_markdown(pytester):
    pytester.makepyfile(
        test_docs="""
        def test_documented_case():
            assert True
        """
    )
    out_file = pytester.path / "docs" / "tests-readable.md"

    result = pytester.runpytest(
        "--collect-only",
        "--readable",
        "--readable-lang=en",
        "--readable-docs",
        "--readable-format=markdown",
        f"--readable-out={out_file}",
        "-q",
    )

    assert out_file.exists()
    assert "# Test Specs" in out_file.read_text(encoding="utf-8")
    result.stdout.fnmatch_lines(["*readable docs exported:*tests-readable.md*"])


@readable(
    intent="Si el plugin puede exportar CSV con encabezados esperados.",
    steps=[
        "Crea un test temporal",
        "Ejecuta pytest en collect-only con formato csv y ruta de salida",
        "Verifica que el archivo exista y tenga encabezado correcto",
    ],
)
def test_plugin_exports_csv(pytester):
    pytester.makepyfile(
        test_docs="""
        def test_documented_case():
            assert True
        """
    )
    out_file = pytester.path / "docs" / "tests-readable.csv"

    pytester.runpytest(
        "--collect-only",
        "--readable",
        "--readable-lang=en",
        "--readable-docs",
        "--readable-format=csv",
        f"--readable-out={out_file}",
        "-q",
    )

    assert out_file.exists()
    assert out_file.read_text(encoding="utf-8").startswith("File,Class,Test,What it tests")


@readable(
    intent="Si readable-lang=es cambia el encabezado del resumen al español.",
    steps=[
        "Crea un test temporal",
        "Ejecuta pytest collect-only con readable e idioma español",
        "Verifica que aparezca Resumen legible",
    ],
)
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
    intent="Ensures --readable-lang=en keeps the readable summary header in English.",
    steps=[
        "Create a temporary test",
        "Run pytest collect-only with readable output and English language",
        "Verify that 'Readable summary' appears",
    ],
)
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
    intent="Si readable-lang=auto detecta idioma desde decorators readable antes de usar entorno.",
    steps=[
        "Fuerza entorno en ingles",
        "Crea un test con readable intent en español",
        "Ejecuta pytest collect-only con readable-lang=auto",
        "Verifica que el encabezado se renderice en español",
    ],
)
def test_plugin_auto_lang_detects_from_decorators(pytester, monkeypatch):
    monkeypatch.setenv("PYTEST_READABLE_LANG", "en_US.UTF-8")
    monkeypatch.setenv("LC_ALL", "en_US.UTF-8")
    monkeypatch.setenv("LANG", "en_US.UTF-8")
    pytester.makepyfile(
        test_auto_lang='''
        from pytest_readable.decorators import readable

        @readable(
            intent="Si detecta idioma español desde decorators",
            steps=["Define metadata en español", "Renderiza en modo auto"],
        )
        def test_detects_es():
            assert True
        '''
    )

    result = pytester.runpytest("--collect-only", "--readable", "--readable-lang=auto", "-q")
    result.stdout.fnmatch_lines(["*Resumen legible*"])


@readable(
    intent="Si un test no tiene metadata readable, el arbol usa el nombre normalizado de la funcion.",
    steps=[
        "Crea un test sin metadata decorada",
        "Ejecuta collect-only con arbol readable",
        "Verifica que el arbol imprima el nombre derivado de la funcion",
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
    intent="Si el resumen detallado respeta idioma por prueba cuando hay metadata bilingue en la misma corrida.",
    steps=[
        "Crea dos pruebas temporales con readable, una en español y otra en ingles",
        "Ejecuta pytest collect-only con readable y include-steps",
        "Verifica que cada caso use labels y estado en su idioma",
    ],
)
def test_plugin_applies_case_language_strategy_in_detailed_list(pytester):
    pytester.makepyfile(
        test_lang='''
        from pytest_readable.decorators import readable

        @readable(
            intent_es="Valida comportamiento en español",
            steps_es=["Ejecuta caso español"],
        )
        def test_case_es():
            assert True

        @readable(
            intent_en="Validates behavior in English",
            steps_en=["Run English case"],
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
    assert "- [recolectadas] test_lang.py::test_case_es" in stdout
    assert "Qué prueba: Valida comportamiento en español" in stdout
    assert "Pasos:" in stdout
    assert "- [collected] test_lang.py::test_case_en" in stdout
    assert "What it tests: Validates behavior in English" in stdout
    assert "Steps:" in stdout


def test_plugin_styles_intent_lines_in_yellow():
    plugin = ReadableRuntimePlugin(config=None)

    assert plugin._line_style("    Qué prueba: valida algo") == {"yellow": True}
    assert plugin._line_style("    What it tests: validates something") == {"yellow": True}
