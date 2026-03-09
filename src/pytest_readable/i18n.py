# Copyright 2026 José Luis López López Prieto and contributors
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

"""i18n helpers that detect the desired language and load gettext catalogs."""

import gettext
import os
from dataclasses import dataclass
from pathlib import Path

from pytest_readable.language_registry import (
    get_language_pack,
    resolve_registered_language,
    supported_languages,
)


LOCALE_DIR = Path(__file__).with_name("locale")
DOMAIN = "pytest_readable"


def normalize_language(language: str | None) -> str:
    """Normalize the language token to one registered code or 'auto'."""
    if not language or language == "auto":
        return "auto"
    resolved = resolve_registered_language(language)
    if resolved is not None:
        return resolved
    default_language = "en" if "en" in supported_languages() else supported_languages()[0]
    return default_language


def resolve_language(preferred: str | None = None) -> str:
    """Decide which language to use, honoring CLI preference then env vars."""
    normalized = normalize_language(preferred)
    if normalized != "auto":
        return normalized

    env_lang = (
        os.environ.get("PYTEST_READABLE_LANG")
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
        labels: list[str] = []
        for language in supported_languages():
            pack = get_language_pack(language)
            if key == "what":
                labels.extend(pack.accepted_what_labels)
            elif key == "steps":
                labels.extend(pack.accepted_steps_labels)
        return tuple(labels)


def get_i18n(preferred: str | None = None) -> I18n:
    """Return an I18n helper configured for the resolved language."""
    language = resolve_language(preferred)
    translations = gettext.translation(
        DOMAIN,
        localedir=LOCALE_DIR,
        languages=[language],
        fallback=True,
    )
    return I18n(language=language, translations=translations)
