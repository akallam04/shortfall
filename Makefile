PYTHON ?= python3
VENV := .venv
VPY := $(VENV)/bin/python

.PHONY: tools venv test lint oversold

tools:
	@git --version
	@go version
	@$(PYTHON) --version
	@gitleaks version
	@openssl version
	@docker --version 2>/dev/null || echo "docker: not installed"
	@docker compose version 2>/dev/null || echo "docker compose: not installed"

venv:
	$(PYTHON) -m venv $(VENV)
	$(VPY) -m pip install --upgrade pip
	$(VPY) -m pip install -e '.[dev]'

test:
	$(VPY) -m pytest

lint:
	$(VPY) -m ruff check .
	$(VPY) -m ruff format --check .

oversold:
	sh scripts/setup-oversold.sh
