# Copyright 2026 LuigiD5555
# Licensed under the MIT License
# See LICENSE file for details.

"""Language registry used by renderers, CLI wrappers, and option choices."""

from dataclasses import asdict, dataclass, fields
from typing import Any, Callable


@dataclass(frozen=True)
class LanguagePack:
    code: str
    summary_title: str
    list_title: str
    what_label: str
    steps_label: str
    criteria_label: str
    missing_criteria_label: str
    display_name_label: str
    final_summary_template: str
    markdown_title: str
    markdown_generated_on: str
    markdown_what_label: str
    markdown_steps_label: str
    markdown_criteria_label: str
    csv_headers: tuple[str, ...]
    status_labels: dict[str, str]
    accepted_what_labels: tuple[str, ...]
    accepted_steps_labels: tuple[str, ...]


LanguagePackFactory = Callable[[], dict[str, Any] | None]


_LANGUAGE_REGISTRY: dict[str, LanguagePack] = {}


def _default_accepted_labels(label: str) -> tuple[str, str]:
    """Return two bold Markdown variants for a given label to recognize localized input."""
    return (f"**{label}:**", f"**{label}**:")


def _build_language_pack(code: str, base: str | None, payload: dict[str, Any]) -> LanguagePack:
    """Assemble and validate a language pack from overrides and optional base values."""
    merged: dict[str, Any] = {}
    if base and base in _LANGUAGE_REGISTRY:
        merged.update(asdict(_LANGUAGE_REGISTRY[base]))

    merged.update(payload)
    merged["code"] = code

    if "what_label" in payload and "accepted_what_labels" not in payload:
        merged["accepted_what_labels"] = _default_accepted_labels(merged["what_label"])
    elif "what_label" in merged:
        merged.setdefault("accepted_what_labels", _default_accepted_labels(merged["what_label"]))

    if "steps_label" in payload and "accepted_steps_labels" not in payload:
        merged["accepted_steps_labels"] = _default_accepted_labels(merged["steps_label"])
    elif "steps_label" in merged:
        merged.setdefault("accepted_steps_labels", _default_accepted_labels(merged["steps_label"]))

    required = {field.name for field in fields(LanguagePack)}
    missing = sorted(required - set(merged))
    if missing:
        missing_fields = ", ".join(missing)
        raise ValueError(f"Missing language pack fields for '{code}': {missing_fields}")

    return LanguagePack(**merged)


def register_language(pack: LanguagePack) -> None:
    """Register or replace a language pack."""
    _LANGUAGE_REGISTRY[pack.code] = pack


def unregister_language(code: str) -> None:
    """Remove a language pack if present."""
    _LANGUAGE_REGISTRY.pop(code, None)


def language_pack(
    code: str, *, base: str | None = None, **overrides: Any
) -> Callable[[LanguagePackFactory], LanguagePackFactory]:
    """Decorator that registers a language pack using optional base inheritance."""

    def _decorator(factory: LanguagePackFactory) -> LanguagePackFactory:
        """Build and register a language pack from `factory` output."""
        factory_payload = factory() or {}
        payload = dict(factory_payload)
        payload.update(overrides)
        register_language(_build_language_pack(code, base, payload))
        return factory

    return _decorator


def supported_languages() -> list[str]:
    """Return registered language codes in registration order."""
    return list(_LANGUAGE_REGISTRY)


def resolve_registered_language(language: str | None) -> str | None:
    """Resolve locale-like tokens (for example es_MX.UTF-8) to a registered code."""
    if not language:
        return None
    normalized = language.strip().lower()
    if not normalized:
        return None

    locale_token = normalized.split(".", 1)[0].replace("-", "_")
    candidates = [locale_token]
    if "_" in locale_token:
        candidates.append(locale_token.split("_", 1)[0])

    for candidate in candidates:
        if candidate in _LANGUAGE_REGISTRY:
            return candidate
    return None


def get_language_pack(language: str | None, fallback: str = "en") -> LanguagePack:
    """Return a language pack, resolving locale variants and fallback defaults."""
    resolved = resolve_registered_language(language)
    if resolved is not None:
        return _LANGUAGE_REGISTRY[resolved]

    if fallback in _LANGUAGE_REGISTRY:
        return _LANGUAGE_REGISTRY[fallback]
    first = next(iter(_LANGUAGE_REGISTRY), None)
    if first is None:
        raise RuntimeError("Language registry is empty.")
    return _LANGUAGE_REGISTRY[first]


def readable_summary_titles() -> set[str]:
    """Return all registered summary titles used to locate readable output blocks."""
    return {pack.summary_title for pack in _LANGUAGE_REGISTRY.values()}


@language_pack("en")
def _register_english() -> dict[str, Any]:
    """Provide the canonical English text values that other languages can base on."""
    return {
        "summary_title": "Readable summary",
        "list_title": "Detailed list",
        "what_label": "What it tests",
        "steps_label": "Steps",
        "criteria_label": "Pass conditions",
        "missing_criteria_label": "No pass conditions documented",
        "display_name_label": "Display name",
        "final_summary_template": "Final summary: total={total}, passed={passed}, failed={failed}, skipped={skipped}",
        "markdown_title": "Test Specs",
        "markdown_generated_on": "Generated on",
        "markdown_what_label": "What it tests",
        "markdown_steps_label": "Steps",
        "markdown_criteria_label": "Pass conditions",
        "csv_headers": ("File", "Class", "Test", "What it tests", "Steps", "Status", "NodeID"),
        "status_labels": {
            "passed": "passed",
            "failed": "failed",
            "skipped": "skipped",
            "error": "error",
            "xfailed": "xfailed",
            "xpassed": "xpassed",
            "deselected": "deselected",
            "warnings": "warnings",
            "no_tests": "no tests ran",
            "collected": "collected",
            "unknown": "unknown",
        },
    }


@language_pack(
    "es",
    base="en",
    summary_title="Resumen legible",
    list_title="Lista detallada",
    what_label="Qué prueba",
    steps_label="Pasos",
    criteria_label="Condiciones para aprobar",
    missing_criteria_label="Sin criterios documentados",
    display_name_label="Nombre mostrado",
    final_summary_template="Resumen final: total={total}, aprobadas={passed}, fallidas={failed}, omitidas={skipped}",
    markdown_title="Especificaciones de tests",
    markdown_generated_on="Generado el",
    markdown_what_label="Si prueba",
    markdown_steps_label="Pasos",
    markdown_criteria_label="Condiciones para aprobar",
    csv_headers=("Archivo", "Clase", "Test", "Si prueba", "Pasos", "Estado", "NodeID"),
    status_labels={
        "passed": "aprobadas",
        "failed": "fallidas",
        "skipped": "omitidas",
        "error": "errores",
        "xfailed": "xfallidas",
        "xpassed": "xaprobadas",
        "deselected": "deseleccionadas",
        "warnings": "advertencias",
        "no_tests": "ningún test corrió",
        "collected": "recolectadas",
        "unknown": "desconocido",
    },
    accepted_what_labels=("**Si prueba:**", "**Si prueba**:", "**Qué prueba:**", "**Qué prueba**:"),
    accepted_steps_labels=("**Pasos:**", "**Pasos**:"),
)
def _register_spanish() -> dict[str, Any] | None:
    """Define the Spanish overrides atop the English base pack."""
    return None
