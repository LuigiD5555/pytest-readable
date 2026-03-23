pytest_plugins = ["pytester"]

import csv
import pytest

from pytest_readable.decorators import readable
from pytest_readable.plugin import ReadableRuntimePlugin


@readable(
    intention="Whether the plugin registers its flags and they appear in pytest help.",
    steps=[
        "Run pytest with help",
        "Look for readable flags in the output",
        "Verify that all expected options are present",
    ],
    criteria=[
        "The help output includes all expected readable flags",
    ],
)
def test_help_exposes_readable_options(pytester):
    result = pytester.runpytest("--help")

    result.stdout.fnmatch_lines(
        [
            "*--readable*",
            "*--detailed, --readable-detailed*",
            "*--readable-verbose*",
            "*--readable-tree*",
            "*--readable-docs*",
            "*--readable-out=PATH*",
            "*--readable-format={markdown,csv}*",
            "*--readable-lang={auto,en,es}*",
            "*--export*",
        ]
    )


@readable(
    intention="Whether readable shows the header and total in the integrated summary.",
    steps=[
        "Create a simple test in a temporary project",
        "Run pytest with readable and readable-lang=en",
        "Verify that the output includes the header and total test count",
    ],
    criteria=[
        "The output contains Readable summary and the correct total",
    ],
)
def test_readable_prints_summary_header_and_total(pytester):
    result = _run_readable_summary(pytester)
    result.stdout.fnmatch_lines(["*Readable summary*", "*- Total: 1*"])


@readable(
    intention="Whether --readable shows a summarized output with nodeid and intention.",
    steps=[
        "Create a simple test in a temporary project",
        "Run pytest with readable and readable-lang=en",
        "Verify that the output includes the summarized list and the case intention",
    ],
    criteria=[
        "The output does not include Steps or Pass conditions",
    ],
)
def test_readable_shows_summarized_block_without_pytest_text(pytester):
    result = _run_readable_summary(pytester)
    stdout = result.stdout.str()
    assert "test session starts" not in stdout
    assert "1 passed" not in stdout
    assert "Detailed list" in stdout
    assert "- [passed] test_sample.py::test_ok" in stdout
    assert "What it tests: test ok" in stdout
    assert "Steps:" not in stdout
    assert "Pass conditions:" not in stdout


@readable(
    intention="Whether --readable-detailed shows intention, steps, and criteria without native pytest output.",
    steps=[
        "Create a simple test in a temporary project",
        "Run pytest with readable-detailed and readable-lang=en",
        "Verify that the detailed list with steps and criteria appears",
    ],
    criteria=[
        "The detailed output includes Steps and Pass conditions",
    ],
)
def test_readable_detailed_hides_pytest_text_and_shows_steps_and_criteria(pytester):
    result = _run_readable_summary(pytester, "--readable-detailed")
    stdout = result.stdout.str()
    assert "test session starts" not in stdout
    assert "1 passed" not in stdout
    assert "Detailed list" in stdout
    assert "Display name: test ok" in stdout
    assert "What it tests: test ok" in stdout
    assert "Steps:" in stdout
    assert "Pass conditions:" in stdout


@readable(
    intention="Whether --readable-verbose adds extra readable context and keeps the native pytest output.",
    steps=[
        "Create a simple test in a temporary project",
        "Run pytest with readable-verbose and readable-lang=en",
        "Verify that the display name, readable summary, and native pytest output appear",
    ],
    criteria=[
        "The verbose output includes Display name and test session starts",
    ],
)
def test_readable_verbose_shows_extra_case_context(pytester):
    result = _run_readable_summary(pytester, "--readable-verbose")
    stdout = result.stdout.str()
    assert "test session starts" in stdout
    assert "1 passed" in stdout
    assert "Display name: test ok" in stdout
    assert "What it tests: test ok" in stdout
    assert "Steps:" in stdout
    assert "Pass conditions:" in stdout


@readable(
    intention="Whether pytest --readable -d enables detailed mode without native pytest output.",
    steps=[
        "Create a simple test in a temporary project",
        "Run pytest with readable and d",
        "Verify that the readable name, steps, and criteria appear without the native header",
    ],
    criteria=[
        "The output matches detailed mode",
    ],
)
def test_readable_short_detailed_alias_matches_detailed_mode(pytester):
    result = _run_readable_summary(pytester, "-d")
    stdout = result.stdout.str()
    assert "test session starts" not in stdout
    assert "Display name: test ok" in stdout
    assert "Steps:" in stdout
    assert "Pass conditions:" in stdout


@readable(
    intention="Whether pytest --readable --detailed enables detailed mode without native pytest output.",
    steps=[
        "Create a simple test in a temporary project",
        "Run pytest with readable and detailed",
        "Verify that the readable name, steps, and criteria appear without the native header",
    ],
    criteria=[
        "The output matches detailed mode",
    ],
)
def test_readable_long_detailed_alias_matches_detailed_mode(pytester):
    result = _run_readable_summary(pytester, "--detailed")
    stdout = result.stdout.str()
    assert "test session starts" not in stdout
    assert "Display name: test ok" in stdout
    assert "Steps:" in stdout
    assert "Pass conditions:" in stdout


@readable(
    intention="Whether pytest --readable -v enables verbose mode.",
    steps=[
        "Create a simple test in a temporary project",
        "Run pytest with readable and v",
        "Verify that the native output is preserved and the display name appears",
    ],
    criteria=[
        "The output matches verbose mode",
    ],
)
def test_readable_short_verbose_alias_matches_verbose_mode(pytester):
    result = _run_readable_summary(pytester, "-v")
    stdout = result.stdout.str()
    assert "test session starts" in stdout
    assert "Display name: test ok" in stdout
    assert "Steps:" in stdout
    assert "Pass conditions:" in stdout


@readable(
    intention="Whether pytest --readable --verbose enables verbose mode.",
    steps=[
        "Create a simple test in a temporary project",
        "Run pytest with readable and verbose",
        "Verify that the native output is preserved and the display name appears",
    ],
    criteria=[
        "The output matches verbose mode",
    ],
)
def test_readable_long_verbose_alias_matches_verbose_mode(pytester):
    result = _run_readable_summary(pytester, "--verbose")
    stdout = result.stdout.str()
    assert "test session starts" in stdout
    assert "Display name: test ok" in stdout
    assert "Steps:" in stdout
    assert "Pass conditions:" in stdout


@readable(
    intention="Whether readable keeps pytest outcomes when running a passing test.",
    steps=[
        "Create a simple test in a temporary project",
        "Run pytest with readable and readable-lang=en",
        "Verify that pytest reports exactly one passing test",
    ],
    criteria=[
        "Pytest reports the test as passed",
    ],
)
def test_readable_prints_summary_reports_passed_outcome(pytester):
    result = _run_readable_summary(pytester)
    assert result.ret == 0
    assert "- passed: 1" in result.stdout.str()


@readable(
    intention="Whether readable still prints pytest's failure and error sections when tests fail.",
    steps=[
        "Create one failing test and one test with a fixture error",
        "Run pytest with readable and readable-lang=en",
        "Verify that pytest prints both FAILURES and ERRORS sections",
    ],
    criteria=[
        "The output includes both failure and error sections",
    ],
)
def test_readable_prints_native_failure_and_error_sections(pytester):
    pytester.makepyfile(
        test_broken="""
        import pytest

        @pytest.fixture
        def broken_fixture():
            raise RuntimeError("boom")

        def test_failing_case():
            assert False

        def test_error_case(broken_fixture):
            del broken_fixture
        """
    )

    result = pytester.runpytest("--readable", "--readable-lang=en")
    stdout = result.stdout.str()
    assert result.ret == 1
    assert "short test summary info" in stdout
    assert "test_failing_case - assert False" in stdout
    assert "test_error_case - RuntimeError: boom" in stdout


def _run_readable_summary(pytester, *extra_args: str):
    pytester.makepyfile(
        test_sample="""
        from pytest_readable.decorators import readable

        @readable(
            intention="test ok",
            steps=["run the test"],
            criteria=["it passes"],
        )
        def test_ok():
            assert True
        """
    )

    args = ["--readable", "--readable-lang=en", *extra_args]
    return pytester.runpytest(*args)


@readable(
    intention="Whether collect-only with readable-tree prints the hierarchy by module and class.",
    steps=[
        "Create a test inside a class",
        "Run pytest in collect-only mode with readable-tree",
        "Verify the module, class, and readable name",
    ],
    criteria=[
        "The tree includes the module, class, and normalized test name",
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
    intention="Whether readable with intention and multiline steps appears in the detailed output.",
    steps=[
        "Create a temporary test with readable intention and multiline steps",
        "Run pytest in collect-only mode with readable include-steps",
        "Verify the header, details, and printed steps",
    ],
    criteria=[
        "The output includes the intention, steps, and documented criteria for the temporary case",
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
    intention="Whether the plugin creates the markdown file when documentation is exported.",
    steps=[
        "Create a temporary test",
        "Run pytest in collect-only mode with markdown format and an output path",
        "Verify that the markdown file exists at the output path",
    ],
    criteria=[
        "The markdown file is created at the specified path",
    ],
)
def test_plugin_exports_markdown_creates_output_file(pytester):
    result, out_file, _ = _export_markdown_docs(pytester)
    assert out_file.exists()
    result.stdout.fnmatch_lines(["*readable docs exported:*tests-readable.md*"])


@readable(
    intention="Whether the exported markdown contains the expected header and case details.",
    steps=[
        "Create a temporary test",
        "Run pytest in collect-only mode with markdown format and an output path",
        "Verify the expected header and fields in the exported content",
    ],
    criteria=[
        "The exported content contains the expected header",
    ],
)
def test_plugin_exports_markdown_includes_expected_content(pytester):
    _, _, rendered = _export_markdown_docs(pytester)
    assert "# Test Specs" in rendered
    assert "- nodeid: `test_docs.py::test_documented_case`" in rendered
    assert "- status: `collected`" in rendered


@readable(
    intention="Whether --export=markdown enables export directly from the new flag.",
    steps=[
        "Create a temporary test",
        "Run pytest collect-only with --readable and --export=markdown",
        "Confirm that the Markdown file is created and the log reports the export",
    ],
    criteria=[
        "The export happens using only the --export flag",
    ],
)
def test_plugin_exports_markdown_with_export_flag(pytester):
    result, out_file, _ = _run_export_docs(pytester, "markdown", via_export_flag=True)
    assert out_file.exists()
    result.stdout.fnmatch_lines(["*readable docs exported:*tests-readable.md*"])


@readable(
    intention="Whether --export=csv creates a CSV export identical to --readable-docs.",
    steps=[
        "Create a temporary test",
        "Run pytest collect-only with --readable and --export=csv",
        "Confirm that the CSV file is generated and the export is reported",
    ],
    criteria=[
        "CSV export works when the --export flag is used",
    ],
)
def test_plugin_exports_csv_with_export_flag(pytester):
    result, out_file, _ = _run_export_docs(pytester, "csv", via_export_flag=True)
    assert out_file.exists()
    result.stdout.fnmatch_lines(["*readable docs exported:*tests-readable.csv*"])


@readable(
    intention="Whether the export runs even when there is a failing test.",
    steps=[
        "Create a temporary test that fails",
        "Run pytest with --readable and --export=markdown",
        "Verify that the output file was created",
    ],
    criteria=[
        "The markdown file is exported even when pytest ends with a failure",
    ],
)
def test_plugin_exports_markdown_even_when_tests_fail(pytester):
    result, out_file = _run_export_docs_with_failure(pytester, "markdown")
    assert out_file.exists()
    assert result.ret == 1
    assert "- failed: 1" in result.stdout.str()
    result.stdout.fnmatch_lines(["*readable docs exported:*tests-readable.md*"])


@readable(
    intention="Whether the export reports the generated file only once per run.",
    steps=[
        "Create a temporary test that passes",
        "Run pytest with --readable and --export=markdown",
        "Count how many times the export message appears in the output",
    ],
    criteria=[
        "The readable docs exported message appears only once",
    ],
)
def test_plugin_reports_export_once_per_run(pytester):
    result, out_file = _run_export_docs_without_collect_only(pytester, "markdown")
    assert out_file.exists()
    assert result.stdout.str().count("readable docs exported:") == 1


def _export_markdown_docs(pytester):
    return _run_export_docs(pytester, "markdown")


@readable(
    intention="Whether the plugin creates the CSV file at the specified path.",
    steps=[
        "Create a temporary test",
        "Run pytest in collect-only mode with csv format and an output path",
        "Verify that the CSV file exists at the output path",
    ],
    criteria=[
        "The CSV file is created at the specified path",
    ],
)
def test_plugin_exports_csv_creates_output_file(pytester):
    _, out_file, _ = _export_csv_docs(pytester)
    assert out_file.exists()


@readable(
    intention="Whether the exported CSV includes the expected headers and columns for the case.",
    steps=[
        "Create a temporary test",
        "Run pytest in collect-only mode with csv format and an output path",
        "Verify the headers and key values in the exported row",
    ],
    criteria=[
        "The CSV header matches the expected columns",
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


def _run_export_docs_without_collect_only(pytester, format_: str):
    pytester.makepyfile(
        test_docs="""
        def test_documented_case():
            assert True
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
    intention_es="Verifica que --readable-lang=es renderiza el encabezado del resumen en español.",
    steps_es=[
        "Crea una prueba temporal",
        "Ejecuta pytest en modo collect-only con salida readable y lenguaje español",
        "Verifica que aparezca 'Resumen legible'",
    ],
    criteria_es=[
        "El encabezado del resumen se renderiza en español",
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
    intention="Verifica que --readable-lang=en mantiene el encabezado del resumen legible en inglés.",
    steps=[
        "Create a temporary test",
        "Run pytest collect-only with readable and English language",
        "Verify that 'Readable summary' appears",
    ],
    criteria=[
        "The summary header is rendered in English",
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


@pytest.mark.auto_lang_only
def test_plugin_auto_lang_detects_language_from_decorator_content_es(pytester):
    pytester.makepyfile(
        test_auto_lang='''
        from pytest_readable.decorators import readable

        @readable(
            intent="Verifica autodeteccion de idioma por contenido del decorator",
            steps=["Define metadata en espanol", "Renderiza el resumen en modo auto"],
            criteria=["Muestra el encabezado en espanol"],
        )
        def test_detects_es():
            assert True
        '''
    )

    result = pytester.runpytest("--collect-only", "--readable", "--readable-lang=auto", "-q")
    result.stdout.fnmatch_lines(["*Resumen legible*"])


@pytest.mark.auto_lang_only
def test_plugin_auto_lang_detects_language_from_decorator_content_en(pytester):
    pytester.makepyfile(
        test_auto_lang_en='''
        from pytest_readable.decorators import readable

        @readable(
            intent="Validates automatic language detection from decorator content",
            steps=["Define metadata in English", "Render the summary in auto mode"],
            criteria=["Shows the header in English"],
        )
        def test_detects_en():
            assert True
        '''
    )

    result = pytester.runpytest("--collect-only", "--readable", "--readable-lang=auto", "-q")
    result.stdout.fnmatch_lines(["*Readable summary*"])


@readable(
    intention="Whether a test without readable metadata uses the normalized function name in the tree.",
    steps=[
        "Create a test without decorated metadata",
        "Run collect-only with the readable tree",
        "Verify that the tree prints the name derived from the function",
    ],
    criteria=[
        "The tree uses the normalized function name when there is no metadata",
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
    intention="Whether the auto detailed summary keeps labels and status in English for both cases.",
    steps=[
        "Create two temporary tests with readable metadata, one in Spanish and one in English",
        "Run pytest collect-only with readable-lang=auto and include-steps",
        "Verify that both cases use English labels and status",
    ],
    criteria=[
        "Both cases use English labels and status",
    ],
)
@pytest.mark.auto_lang_only
def test_plugin_applies_case_language_strategy_in_detailed_list_es(pytester):
    stdout = _run_case_language_strategy(pytester)
    assert "- [collected] test_lang.py::test_case_es" in stdout
    assert "What it tests: Valida comportamiento en español" in stdout
    assert "Steps:" in stdout


@readable(
    intention_es="Verifica que el caso en inglés use las etiquetas del idioma de output (inglés) cuando readable-lang=auto detecta inglés.",
    steps_es=[
        "Crea dos pruebas temporales con metadata readable en español e inglés",
        "Ejecuta pytest en modo collect-only con readable-lang=auto e include-steps",
        "Verifica que el caso en inglés use etiquetas inglesas porque el output es inglés",
    ],
    criteria_es=[
        "El caso en inglés muestra etiquetas en inglés cuando el output language es inglés",
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
    intention="Whether readable-lang=en forces labels and metadata into English even when the decorator contains Spanish content.",
    steps=[
        "Create a temporary test with readable metadata in Spanish",
        "Run pytest collect-only with readable-lang=en and include-steps",
        "Verify that the status, labels, and content are rendered in English",
    ],
    criteria=[
        "The output uses English labels and content even though the original metadata is in Spanish",
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
    intention="Whether readable-lang=es forces labels and metadata into Spanish even when the decorator contains English content.",
    steps=[
        "Create a temporary test with readable metadata in English",
        "Run pytest collect-only with readable-lang=es and include-steps",
        "Verify that the status, labels, and content are rendered in Spanish",
    ],
    criteria=[
        "The output uses Spanish labels and content even though the original metadata is in English",
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
    intention="Whether the plugin applies yellow color to intention lines in both languages.",
    steps=[
        "Create a runtime plugin instance",
        "Evaluate the style for a Spanish line and an English line",
        "Verify that both return yellow coloring",
    ],
    criteria=[
        "\"What it tests\" is colored yellow in ANSI output",
    ],
)
def test_plugin_styles_intention_lines_in_yellow():
    plugin = ReadableRuntimePlugin(config=None)

    assert plugin._line_style("    Qué prueba: valida algo") == {"yellow": True}
    assert plugin._line_style("    What it tests: validates something") == {"yellow": True}
    assert plugin._line_style("    Condiciones para aprobar:") == {"blue": True}
    assert plugin._line_style("    Pass conditions:") == {"blue": True}


@readable(
    intention="Whether the plugin report colors the criteria header blue in ANSI output.",
    steps=[
        "Create a temporary test with criteria metadata",
        "Run pytest collect-only with readable and forced color",
        "Verify that the criteria line is printed with the blue ANSI code",
    ],
    criteria=[
        "The output contains \"Pass conditions\" with a blue ANSI sequence",
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


@readable(
    intention="Whether an xfail test is tracked as xfailed and not as skipped.",
    steps=[
        "Create a test marked with pytest.mark.xfail that fails as expected",
        "Run pytest with --readable and --readable-lang=en",
        "Verify that the final summary shows xfailed=1 and skipped=0",
    ],
    criteria=[
        "The final summary line shows xfailed=1",
        "skipped does not appear in the final summary",
    ],
)
def test_xfail_outcome_is_tracked_as_xfailed(pytester):
    pytester.makepyfile(
        test_xfail="""
        import pytest

        @pytest.mark.xfail
        def test_expected_failure():
            assert False
        """
    )

    result = pytester.runpytest("--readable", "--readable-lang=en")
    stdout = result.stdout.str()
    assert "xfailed=1" in stdout
    final_summary = stdout.split("Final summary")[-1]
    assert "skipped=0" in final_summary
    assert "xfailed=1" in final_summary


@readable(
    intention="Whether an xpass test is tracked as xpassed and not as passed.",
    steps=[
        "Create a test marked with pytest.mark.xfail that passes unexpectedly",
        "Run pytest with --readable and --readable-lang=en",
        "Verify that the final summary shows xpassed=1 and passed=0",
    ],
    criteria=[
        "The final summary line shows xpassed=1",
        "passed=0 appears in the final summary",
    ],
)
def test_xpass_outcome_is_tracked_as_xpassed(pytester):
    pytester.makepyfile(
        test_xpass="""
        import pytest

        @pytest.mark.xfail
        def test_unexpected_pass():
            assert True
        """
    )

    result = pytester.runpytest("--readable", "--readable-lang=en")
    stdout = result.stdout.str()
    assert "xpassed=1" in stdout
    assert "passed=0" in stdout.split("Final summary")[-1]
