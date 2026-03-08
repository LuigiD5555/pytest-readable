PYTHON ?= python3
PIP ?= $(PYTHON) -m pip
PYTEST ?= $(PYTHON) -m pytest

.PHONY: install install-dev test test-readable-core verify-core

install:
	$(PIP) install -e .

install-dev:
	$(PIP) install -U pip
	$(PIP) install -e .

test:
	$(PYTEST) -q

test-readable-core:
	$(PYTEST) -q tests/test_core.py

verify-core: install test-readable-core
