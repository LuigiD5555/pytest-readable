pytest_plugins = ["pytester"]


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


def test_readable_prints_summary(pytester):
    pytester.makepyfile(
        test_sample="""
        def test_ok():
            assert True
        """
    )

    result = pytester.runpytest("--readable", "-q")

    result.stdout.fnmatch_lines(["*Readable summary*", "*- Total: 1*"])
    result.assert_outcomes(passed=1)


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
        "--readable-docs",
        "--readable-format=markdown",
        f"--readable-out={out_file}",
        "-q",
    )

    assert out_file.exists()
    assert "# Test Specs" in out_file.read_text(encoding="utf-8")
    result.stdout.fnmatch_lines(["*readable docs exported:*tests-readable.md*"])


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
        "--readable-docs",
        "--readable-format=csv",
        f"--readable-out={out_file}",
        "-q",
    )

    assert out_file.exists()
    assert out_file.read_text(encoding="utf-8").startswith("File,Class,Test,What it tests")


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


def test_plugin_uses_spec_markdown_fallback_for_tree_name(pytester):
    pytester.makepyfile(
        test_query="""
        def test_blackboard_pipeline():
            assert True
        """
    )
    pytester.makefile(
        ".spec.md",
        test_query="""# test_query.py

## Pipeline de consulta
**Qué prueba:** Describe el flujo principal
**Pasos:**
1. Embedding
2. Retrieval
3. Blackboard
""",
    )

    result = pytester.runpytest(
        "--collect-only",
        "--readable-tree",
        "--readable-lang=es",
        "-q",
    )

    result.stdout.fnmatch_lines(["*Pipeline de consulta*"])
