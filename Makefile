PYTHON ?= python3
PIP ?= $(PYTHON) -m pip
PYTEST ?= $(PYTHON) -m pytest

.PHONY: install install-dev test test-translator-i18n verify-i18n

install:
	$(PIP) install -e .

install-dev:
	$(PIP) install -U pip
	$(PIP) install -e .

test:
	$(PYTEST) -q

test-translator-i18n:
	$(PYTEST) -q tests/test_i18n.py

verify-i18n: install test-translator-i18n
