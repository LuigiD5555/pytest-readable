"""Helpers that normalize decorator/markdown specs and build readable suites."""

import ast
import re
from pathlib import Path
from typing import Any

from pytest_readable.core.models import ReadableSuite, ReadableTestCase
from pytest_readable.i18n import I18n


def find_spec_files(root: Path) -> list[Path]:
    """Locate all `.spec.md` files beneath the given directory."""
    return sorted(root.rglob("*.spec.md"))


def find_test_files(root: Path) -> list[Path]:
    """Collect pytest-style test files under the directory."""
    paths = set(root.rglob("test_*.py"))
    paths.update(root.rglob("*_test.py"))
    return sorted(paths)


def parse_spec_file(path: Path, i18n: I18n) -> dict[str, Any]:
    """Parse a `.spec.md` document into a normalized structure for rendering."""
    content = path.read_text(encoding="utf-8")
    lines = content.splitlines()

    result: dict[str, Any] = {
        "file": path,
        "title": "",
        "tests": [],
    }

    current_test = None
    in_steps = False
    what_labels = i18n.accepted_field_labels("what")
    steps_labels = i18n.accepted_field_labels("steps")

    for line in lines:
        stripped = line.strip()

        if stripped.startswith("# ") and not result["title"]:
            result["title"] = stripped[2:].strip()
            continue

        if stripped.startswith("## "):
            if current_test:
                result["tests"].append(current_test)
            current_test = {
                "name": stripped[3:].strip(),
                "what": "",
                "steps": [],
            }
            in_steps = False
            continue

        if current_test is None:
            continue

        matched_label = next((label for label in what_labels if stripped.startswith(label)), None)
        if matched_label is not None:
            current_test["what"] = stripped[len(matched_label):].strip()
            in_steps = False
            continue

        if stripped in steps_labels:
            in_steps = True
            continue

        if in_steps and stripped:
            step_match = re.match(r"^(\d+\.|-)\s+(.*)", stripped)
            if step_match:
                current_test["steps"].append(step_match.group(2).strip())

    if current_test:
        result["tests"].append(current_test)

    return result


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


def _pick_steps(call: ast.Call, language: str) -> list[str]:
    """Select a list of step strings from the decorator, respecting language."""
    for candidate in (f"steps_{language}", "steps", "steps_en", "steps_es"):
        value = _kwarg(call, candidate)
        if isinstance(value, list):
            return [str(item) for item in value]
    return []


def _parse_decorated_test(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    language: str,
    class_name: str = "",
) -> dict[str, Any] | None:
    """Extract metadata from a single decorated pytest test function."""
    if not node.name.startswith("test"):
        return None

    spec_call = None
    for decorator in node.decorator_list:
        if _decorator_name(decorator) == "spec" and isinstance(decorator, ast.Call):
            spec_call = decorator
            break
    if spec_call is None:
        return None

    default_name = f"{class_name}.{node.name}" if class_name else node.name
    name = _pick_text(spec_call, "title", language) or default_name.replace("_", " ")
    what = _pick_text(spec_call, "what", language)
    steps = _pick_steps(spec_call, language)

    return {"name": name, "what": what, "steps": steps}


def parse_decorated_spec_file(path: Path, language: str) -> dict[str, Any]:
    """Walk a test module to collect all `@spec` decorator metadata."""
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


def _spec_md_path_for_test(test_path: Path) -> Path:
    """Derive the companion spec markdown path for a given test file."""
    return test_path.with_name(f"{test_path.stem}.spec.md")


def generate_spec_markdown_from_decorators(root: Path, i18n: I18n) -> list[Path]:
    """Emit `.spec.md` files by translating decorator metadata for each test file."""
    generated = []
    for test_file in find_test_files(root):
        spec = parse_decorated_spec_file(test_file, i18n.language)
        if not spec["tests"]:
            continue

        lines = [f"# {spec['title']}", ""]
        for test in spec["tests"]:
            lines.append(f"## {test['name']}")
            if test["what"]:
                lines.append(f"**{i18n.field_label('what')}:** {test['what']}")
            if test["steps"]:
                lines.append(f"**{i18n.field_label('steps')}:**")
                for i, step in enumerate(test["steps"], 1):
                    lines.append(f"{i}. {step}")
            lines.append("")

        output_path = _spec_md_path_for_test(test_file)
        output_path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")
        generated.append(output_path)

    return generated


def load_specs(root: Path, i18n: I18n) -> list[dict[str, Any]]:
    """Load spec metadata preferring decorators and falling back to `.spec.md`."""
    decorated_specs = []
    decorated_files = set()
    for test_file in find_test_files(root):
        spec = parse_decorated_spec_file(test_file, i18n.language)
        if spec["tests"]:
            decorated_specs.append(spec)
            decorated_files.add(test_file.resolve())

    markdown_specs = []
    for spec_file in find_spec_files(root):
        candidate_test = spec_file.with_name(spec_file.name.replace(".spec.md", ".py")).resolve()
        if candidate_test in decorated_files:
            continue
        markdown_specs.append(parse_spec_file(spec_file, i18n))

    return sorted(decorated_specs + markdown_specs, key=lambda spec: str(spec["file"]))


def _normalize_key(value: str) -> str:
    """Normalize text for best-effort comparison between names."""
    lowered = value.lower().replace("test_", "")
    return re.sub(r"[^a-z0-9]", "", lowered)


def _pick_value(metadata: dict[str, Any], key: str, language: str) -> str:
    """Choose the most specific localized string from metadata."""
    for candidate in (f"{key}_{language}", key, f"{key}_en", f"{key}_es"):
        value = metadata.get(candidate)
        if isinstance(value, str) and value:
            return value
    return ""


def _pick_steps_from_metadata(metadata: dict[str, Any], language: str) -> list[str]:
    """Return localized step lists stored on the decorated function."""
    for candidate in (f"steps_{language}", "steps", "steps_en", "steps_es"):
        value = metadata.get(candidate)
        if isinstance(value, list):
            return [str(step) for step in value]
    return []


def _normalize_function_name(function_name: str) -> str:
    """Turn a pytest function name into a human-readable string."""
    return function_name.replace("test_", "").replace("_", " ").strip() or function_name


def _read_markdown_index(rootdir: Path, i18n: I18n) -> dict[Path, list[dict[str, Any]]]:
    """Index `.spec.md` content so it can be matched to pytest items."""
    mapping: dict[Path, list[dict[str, Any]]] = {}
    for spec_file in find_spec_files(rootdir):
        parsed = parse_spec_file(spec_file, i18n)
        test_candidate = (spec_file.parent / spec_file.name.replace(".spec.md", ".py")).resolve()
        mapping[test_candidate] = parsed["tests"]
    return mapping


def _pick_markdown_entry(
    file_entries: list[dict[str, Any]],
    used_indexes: set[int],
    function_name: str,
) -> dict[str, Any] | None:
    """Match a markdown entry to a collected test function name if possible."""
    fn_key = _normalize_key(function_name)
    for idx, entry in enumerate(file_entries):
        if idx in used_indexes:
            continue
        entry_key = _normalize_key(entry.get("name", ""))
        if entry_key and (entry_key in fn_key or fn_key in entry_key):
            used_indexes.add(idx)
            return entry

    for idx, entry in enumerate(file_entries):
        if idx not in used_indexes:
            used_indexes.add(idx)
            return entry
    return None


def build_suite_from_items(items: list[Any], rootdir: Path, i18n: I18n) -> ReadableSuite:
    """Build a readable suite model that mirrors pytest's collected order."""
    markdown_index = _read_markdown_index(rootdir, i18n)
    markdown_usage: dict[Path, set[int]] = {}

    cases: list[ReadableTestCase] = []
    for item in items:
        path = Path(str(getattr(item, "path", ""))).resolve()
        class_name = item.cls.__name__ if getattr(item, "cls", None) else ""
        function_name = getattr(item, "originalname", None) or item.name.split("[", 1)[0]
        metadata = getattr(getattr(item, "obj", None), "__spec_meta__", {}) or {}

        display_name = _pick_value(metadata, "title", i18n.language) or _normalize_function_name(function_name)
        what = _pick_value(metadata, "what", i18n.language)
        steps = _pick_steps_from_metadata(metadata, i18n.language)

        if not what and not steps:
            entries = markdown_index.get(path, [])
            if entries:
                used = markdown_usage.setdefault(path, set())
                picked = _pick_markdown_entry(entries, used, function_name)
                if picked is not None:
                    display_name = picked.get("name") or display_name
                    what = picked.get("what", "")
                    steps = list(picked.get("steps", []))

        module_path = str(path.relative_to(rootdir)) if path.is_relative_to(rootdir) else str(path)

        cases.append(
            ReadableTestCase(
                nodeid=item.nodeid,
                module_path=module_path,
                class_name=class_name,
                function_name=function_name,
                display_name=display_name,
                what=what,
                steps=steps,
                markers=[marker.name for marker in item.iter_markers()],
            )
        )

    return ReadableSuite(rootdir=rootdir, language=i18n.language, cases=cases)
