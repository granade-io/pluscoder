VENV_DIR := .venv
REQUIREMENTS_FILE := requirements.txt
PRECOMMIT_CONFIG := .pre-commit-config.yaml

.PHONY: venv install_requirements precommit install_precommit

venv:
	@if [ ! -d $(VENV_DIR) ]; then \
		echo "Creating virtual environment..."; \
		python3 -m venv $(VENV_DIR); \
	else \
		echo "Virtual environment already exists."; \
	fi

install: venv
	@echo "Installing requirements from $(REQUIREMENTS_FILE)..."
	@pip install -r $(REQUIREMENTS_FILE)

install-dev: venv
	@echo "Installing dev requirements from $(REQUIREMENTS_FILE)..."
	@pip install -r requirements.txt requirements-dev.txt

editable:
	@echo "Installing package in editable mode..."
	@pip install -e .

precommit-setup:
	@echo "Installing pre-commit..."
	@pip install pre-commit
	@if [ -f $(PRECOMMIT_CONFIG) ]; then \
		echo "Installing pre-commit hooks..."; \
		pre-commit install; \
	else \
		echo "$(PRECOMMIT_CONFIG) not found. Please create one."; \
	fi

precommit:
	@echo "Running pre-commit on all files..."
	@pre-commit run --all-files

fmt:
	@echo "Running ruff..."
	@ruff format .

test:
	@echo "Running tests..."
	@pytest -v tests