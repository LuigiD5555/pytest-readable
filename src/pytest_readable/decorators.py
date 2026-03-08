def spec(
    *,
    title: str = "",
    title_en: str = "",
    title_es: str = "",
    what: str = "",
    what_en: str = "",
    what_es: str = "",
    steps: list[str] | None = None,
    steps_en: list[str] | None = None,
    steps_es: list[str] | None = None,
):
    """Attach readable metadata to a pytest test function."""
    metadata = {
        "title": title,
        "title_en": title_en,
        "title_es": title_es,
        "what": what,
        "what_en": what_en,
        "what_es": what_es,
        "steps": list(steps or []),
        "steps_en": list(steps_en or []),
        "steps_es": list(steps_es or []),
    }

    def _decorator(function):
        function.__spec_meta__ = metadata
        return function

    return _decorator
