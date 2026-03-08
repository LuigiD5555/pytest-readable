import gettext
import os
from dataclasses import dataclass
from pathlib import Path


LOCALE_DIR = Path(__file__).with_name("locale")
DOMAIN = "pytest_translator"

FIELD_LABELS = {
    "what": {
        "en": ("**What it tests:**",),
        "es": ("**Que prueba:**", "**Que prueba**:", "**Qué prueba:**", "**Qué prueba**:"),
    },
    "steps": {
        "en": ("**Steps:**", "**Steps**:"),
        "es": ("**Pasos:**", "**Pasos**:"),
    },
}


def normalize_language(language: str | None) -> str:
    if not language or language == "auto":
        return "auto"
    normalized = language.lower()
    if normalized.startswith("es"):
        return "es"
    return "en"


def detect_language_from_text(text: str) -> str | None:
    scores = {"en": 0, "es": 0}
    for labels_by_language in FIELD_LABELS.values():
        for language, labels in labels_by_language.items():
            for label in labels:
                scores[language] += text.count(label)

    if scores["en"] == scores["es"] == 0:
        return None
    if scores["en"] == scores["es"]:
        return None
    return max(scores, key=scores.get)


def detect_language_from_specs(spec_files: list[Path]) -> str | None:
    scores = {"en": 0, "es": 0}
    for path in spec_files:
        detected = detect_language_from_text(path.read_text(encoding="utf-8"))
        if detected:
            scores[detected] += 1

    if scores["en"] == scores["es"] == 0:
        return None
    if scores["en"] == scores["es"]:
        return None
    return max(scores, key=scores.get)


def resolve_language(preferred: str | None = None, spec_files: list[Path] | None = None) -> str:
    normalized = normalize_language(preferred)
    if normalized != "auto":
        return normalized

    if spec_files:
        detected = detect_language_from_specs(spec_files)
        if detected:
            return detected

    env_lang = (
        os.environ.get("PYTEST_TRANSLATOR_LANG")
        or os.environ.get("LC_ALL")
        or os.environ.get("LANG")
        or ""
    )
    normalized_env = normalize_language(env_lang)
    if normalized_env != "auto":
        return normalized_env
    return "en"


@dataclass(frozen=True)
class I18n:
    language: str
    translations: gettext.NullTranslations

    def t(self, message: str, **kwargs) -> str:
        text = self.translations.gettext(message)
        if kwargs:
            return text.format(**kwargs)
        return text

    def field_label(self, key: str) -> str:
        return self.t(f"{key}_label")

    def accepted_field_labels(self, key: str) -> tuple[str, ...]:
        labels = []
        for variants in FIELD_LABELS[key].values():
            labels.extend(variants)
        return tuple(labels)


def get_i18n(preferred: str | None = None, spec_files: list[Path] | None = None) -> I18n:
    language = resolve_language(preferred, spec_files=spec_files)
    translations = gettext.translation(
        DOMAIN,
        localedir=LOCALE_DIR,
        languages=[language],
        fallback=True,
    )
    return I18n(language=language, translations=translations)
