"""Helpers that normalize decorator metadata and build readable suites."""

import ast
from pathlib import Path
from typing import Any

from pytest_readable.core.models import ReadableSuite, ReadableTestCase
from pytest_readable.i18n import I18n


def find_test_files(root: Path) -> list[Path]:
    """Collect pytest-style test files under the directory."""
    paths = set(root.rglob("test_*.py"))
    paths.update(root.rglob("*_test.py"))
    return sorted(paths)


def _has_value(value: Any) -> bool:
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, list):
        return any(str(item).strip() for item in value)
    return False


def _score_text_language(text: str) -> tuple[int, int]:
    sample = text.lower()
    en_score = 0
    es_score = 0

    if any(ch in sample for ch in ("á", "é", "í", "ó", "ú", "ñ")):
        es_score += 2

    es_tokens = (
        " que ",
        " prueba",
        " pasos",
        " español",
        " español",
        " verifica",
        " ejecuta",
        " construye",
        " idioma",
        " resumen",
        " archivo",
    )
    en_tokens = (
        " the ",
        " what ",
        " steps",
        " english",
        " verify",
        " run ",
        " build",
        " language",
        " summary",
        " file",
    )

    for token in es_tokens:
        if token in sample:
            es_score += 1
    for token in en_tokens:
        if token in sample:
            en_score += 1

    return en_score, es_score


def detect_language_from_decorators(root: Path) -> str | None:
    """Infer predominant language from `@readable(...)` metadata in test files."""
    scores = {"en": 0, "es": 0}

    for test_file in find_test_files(root):
        tree = ast.parse(test_file.read_text(encoding="utf-8"), filename=str(test_file))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if _decorator_name(node) != "readable":
                continue

            for keyword in node.keywords:
                if keyword.arg is None:
                    continue
                value = _literal(keyword.value)
                if not _has_value(value):
                    continue

                if keyword.arg.endswith("_es"):
                    scores["es"] += 3
                    continue
                if keyword.arg.endswith("_en"):
                    scores["en"] += 3
                    continue
                if keyword.arg not in {"intent", "title", "steps", "criteria"}:
                    continue

                if isinstance(value, list):
                    joined = " ".join(str(item) for item in value)
                else:
                    joined = str(value)
                en_score, es_score = _score_text_language(joined)
                scores["en"] += en_score
                scores["es"] += es_score

    if scores["en"] == scores["es"] == 0:
        return None
    if scores["en"] == scores["es"]:
        return None
    return "en" if scores["en"] > scores["es"] else "es"


def _decorator_name(decorator: ast.expr) -> str:
    """Return the identifier of the decorator (handles dotted calls)."""
    target = decorator.func if isinstance(decorator, ast.Call) else decorator
    if isinstance(target, ast.Name):
        return target.id
    if isinstance(target, ast.Attribute):
        return target.attr
    return ""


def _literal(node: ast.expr):
    """Safely evaluate an AST literal, returning None on failure."""
    try:
        return ast.literal_eval(node)
    except (ValueError, TypeError, SyntaxError):
        return None


def _kwarg(call: ast.Call, key: str):
    """Return the literal value for a keyword argument inside a decorator call."""
    for keyword in call.keywords:
        if keyword.arg == key:
            return _literal(keyword.value)
    return None


def _pick_text(call: ast.Call, key: str, language: str) -> str:
    """Select the localized string argument for the decorator metadata."""
    for candidate in (f"{key}_{language}", key, f"{key}_en", f"{key}_es"):
        value = _kwarg(call, candidate)
        if isinstance(value, str):
            return value
    return ""


def _parse_steps_text(value: str) -> list[str]:
    """Parse multiline steps text supporting numbered and bullet style input."""
    steps: list[str] = []
    for raw_line in value.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        line = line.lstrip("-").strip()
        if ". " in line and line.split(". ", 1)[0].isdigit():
            line = line.split(". ", 1)[1].strip()
        steps.append(line)
    return steps


def _pick_steps(call: ast.Call, language: str) -> list[str]:
    """Select step metadata as list or multiline string from the decorator."""
    for candidate in (f"steps_{language}", "steps", "steps_en", "steps_es"):
        value = _kwarg(call, candidate)
        if isinstance(value, list):
            normalized = [str(item) for item in value]
            if normalized:
                return normalized
            continue
        if isinstance(value, str):
            normalized = _parse_steps_text(value)
            if normalized:
                return normalized
            continue
    return []


def _pick_criteria(call: ast.Call, language: str) -> list[str]:
    """Select pass-condition metadata as list or multiline string."""
    for candidate in (f"criteria_{language}", "criteria", "criteria_en", "criteria_es"):
        value = _kwarg(call, candidate)
        if isinstance(value, list):
            normalized = [str(item) for item in value]
            if normalized:
                return normalized
            continue
        if isinstance(value, str):
            normalized = _parse_steps_text(value)
            if normalized:
                return normalized
            continue
    return []


def _parse_decorated_test(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    language: str,
    class_name: str = "",
) -> dict[str, Any] | None:
    """Extract metadata from a single decorated pytest test function."""
    if not node.name.startswith("test"):
        return None

    readable_call = None
    for decorator in node.decorator_list:
        if _decorator_name(decorator) == "readable" and isinstance(decorator, ast.Call):
            readable_call = decorator
            break
    if readable_call is None:
        return None

    default_name = f"{class_name}.{node.name}" if class_name else node.name
    name = _pick_text(readable_call, "title", language) or default_name.replace("_", " ")
    what = _pick_text(readable_call, "intent", language)
    steps = _pick_steps(readable_call, language)
    criteria = _pick_criteria(readable_call, language)

    return {"name": name, "what": what, "steps": steps, "criteria": criteria}


def parse_decorated_spec_file(path: Path, language: str) -> dict[str, Any]:
    """Walk a test module to collect all `@readable` decorator metadata."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    tests = []

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            parsed = _parse_decorated_test(node, language)
            if parsed:
                tests.append(parsed)
            continue

        if isinstance(node, ast.ClassDef) and node.name.startswith("Test"):
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    parsed = _parse_decorated_test(child, language, class_name=node.name)
                    if parsed:
                        tests.append(parsed)

    return {"file": path, "title": path.name, "tests": tests}


def _pick_value(metadata: dict[str, Any], key: str, language: str) -> str:
    """Choose the most specific localized string from metadata."""
    for candidate in (f"{key}_{language}", key, f"{key}_en", f"{key}_es"):
        value = metadata.get(candidate)
        if isinstance(value, str) and value:
            return value
    return ""


def _text_chunks(value: Any) -> list[str]:
    if isinstance(value, str) and value.strip():
        return [value]
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    return []


def _infer_metadata_language(metadata: dict[str, Any], default_language: str) -> str:
    """Infer language preference for one decorated test metadata payload."""
    scores = {"en": 0, "es": 0}

    for key in ("title", "intent", "steps", "criteria"):
        en_chunks = _text_chunks(metadata.get(f"{key}_en"))
        es_chunks = _text_chunks(metadata.get(f"{key}_es"))
        if en_chunks:
            scores["en"] += 3
        if es_chunks:
            scores["es"] += 3

        generic_chunks = _text_chunks(metadata.get(key))
        for chunk in generic_chunks:
            en_score, es_score = _score_text_language(chunk)
            scores["en"] += en_score
            scores["es"] += es_score

    if scores["en"] == scores["es"]:
        return default_language
    return "en" if scores["en"] > scores["es"] else "es"


def _pick_steps_from_metadata(metadata: dict[str, Any], language: str) -> list[str]:
    """Return localized step lists stored on the decorated function."""
    for candidate in (f"steps_{language}", "steps", "steps_en", "steps_es"):
        value = metadata.get(candidate)
        if isinstance(value, list):
            normalized = [str(step) for step in value]
            if normalized:
                return normalized
            continue
    return []


def _pick_criteria_from_metadata(metadata: dict[str, Any], language: str) -> list[str]:
    """Return localized pass-condition lists stored on the decorated function."""
    for candidate in (f"criteria_{language}", "criteria", "criteria_en", "criteria_es"):
        value = metadata.get(candidate)
        if isinstance(value, list):
            normalized = [str(step) for step in value]
            if normalized:
                return normalized
            continue
    return []


def _normalize_function_name(function_name: str) -> str:
    """Turn a pytest function name into a human-readable string."""
    return function_name.replace("test_", "").replace("_", " ").strip() or function_name


def build_suite_from_items(
    items: list[Any],
    rootdir: Path,
    i18n: I18n,
    preserve_case_language: bool = False,
) -> ReadableSuite:
    """Build a readable suite model that mirrors pytest's collected order."""
    cases: list[ReadableTestCase] = []
    for item in items:
        path = Path(str(getattr(item, "path", ""))).resolve()
        class_name = item.cls.__name__ if getattr(item, "cls", None) else ""
        function_name = getattr(item, "originalname", None) or item.name.split("[", 1)[0]
        metadata = getattr(getattr(item, "obj", None), "__spec_meta__", {}) or {}
        case_language = i18n.language
        if preserve_case_language:
            case_language = _infer_metadata_language(metadata, i18n.language)

        intent = _pick_value(metadata, "intent", case_language)
        display_name = intent or _pick_value(metadata, "title", case_language) or _normalize_function_name(
            function_name
        )
        what = intent
        steps = _pick_steps_from_metadata(metadata, case_language)
        criteria = _pick_criteria_from_metadata(metadata, case_language)

        module_path = str(path.relative_to(rootdir)) if path.is_relative_to(rootdir) else str(path)

        cases.append(
            ReadableTestCase(
                nodeid=item.nodeid,
                module_path=module_path,
                class_name=class_name,
                function_name=function_name,
                display_name=display_name,
                language=case_language,
                what=what,
                steps=steps,
                criteria=criteria,
                markers=[marker.name for marker in item.iter_markers()],
            )
        )

    return ReadableSuite(rootdir=rootdir, language=i18n.language, cases=cases)
