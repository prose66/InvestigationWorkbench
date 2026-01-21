.PHONY: dev install test lint format clean help

VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
STREAMLIT := $(VENV)/bin/streamlit
PYTEST := $(VENV)/bin/pytest
RUFF := $(VENV)/bin/ruff

help:
	@echo "Investigation Workbench - Development Commands"
	@echo ""
	@echo "  make install    Install dependencies in virtual environment"
	@echo "  make dev        Start the Streamlit development server"
	@echo "  make test       Run the test suite"
	@echo "  make lint       Check code with ruff"
	@echo "  make format     Format code with ruff"
	@echo "  make clean      Remove build artifacts and caches"
	@echo ""

install: $(VENV)/bin/activate
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

$(VENV)/bin/activate:
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip

dev: $(VENV)/bin/activate
	$(STREAMLIT) run app/main.py

test: $(VENV)/bin/activate
	$(PYTEST) tests/ -v

lint: $(VENV)/bin/activate
	$(RUFF) check .

format: $(VENV)/bin/activate
	$(RUFF) format .
	$(RUFF) check --fix .

clean:
	rm -rf __pycache__ */__pycache__ */*/__pycache__
	rm -rf .pytest_cache .ruff_cache
	rm -rf *.egg-info dist build

# CLI shortcuts
init-case: $(VENV)/bin/activate
	$(PYTHON) -m cli init-case $(ARGS)

add-run: $(VENV)/bin/activate
	$(PYTHON) -m cli add-run $(ARGS)

ingest-run: $(VENV)/bin/activate
	$(PYTHON) -m cli ingest-run $(ARGS)

ingest-all: $(VENV)/bin/activate
	$(PYTHON) -m cli ingest-all $(ARGS)

export-timeline: $(VENV)/bin/activate
	$(PYTHON) -m cli export-timeline $(ARGS)
