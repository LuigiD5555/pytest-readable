# Copyright 2026 José Luis López López Prieto and contributors
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

"""pytest_readable: native pytest plugin for readable test documentation."""

__version__ = "0.1.0"

from pytest_readable.decorators import readable
from pytest_readable.language_registry import LanguagePack, language_pack, register_language

__all__ = ["readable", "LanguagePack", "language_pack", "register_language", "__version__"]
