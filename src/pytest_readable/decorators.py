def _normalize_lines(values: list[str] | str | None) -> list[str]:
    """Accept list or multiline text and return normalized non-empty lines."""
    if values is None:
        return []
    if isinstance(values, str):
        normalized: list[str] = []
        for raw_line in values.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            line = line.lstrip("-").strip()
            if ". " in line and line.split(". ", 1)[0].isdigit():
                line = line.split(". ", 1)[1].strip()
            normalized.append(line)
        return normalized
    return [str(item).strip() for item in values if str(item).strip()]


def readable(
    *,
    title: str = "",
    title_en: str = "",
    title_es: str = "",
    intent: str = "",
    intent_en: str = "",
    intent_es: str = "",
    steps: list[str] | str | None = None,
    steps_en: list[str] | str | None = None,
    steps_es: list[str] | str | None = None,
    criteria: list[str] | str | None = None,
    criteria_en: list[str] | str | None = None,
    criteria_es: list[str] | str | None = None,
):
    """Attach readable metadata to a pytest test function."""
    metadata = {
        "title": title,
        "title_en": title_en,
        "title_es": title_es,
        "intent": intent,
        "intent_en": intent_en,
        "intent_es": intent_es,
        "steps": _normalize_lines(steps),
        "steps_en": _normalize_lines(steps_en),
        "steps_es": _normalize_lines(steps_es),
        "criteria": _normalize_lines(criteria),
        "criteria_en": _normalize_lines(criteria_en),
        "criteria_es": _normalize_lines(criteria_es),
    }

    def _decorator(function):
        function.__spec_meta__ = metadata
        return function

    return _decorator
