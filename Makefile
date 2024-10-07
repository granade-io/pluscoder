VENV_DIR := .venv
REQUIREMENTS_FILE := requirements.txt
PRECOMMIT_CONFIG := .pre-commit-config.yaml
RUFF_CONFIG := ruff.toml

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
	@$(VENV_DIR)/bin/pip install -r $(REQUIREMENTS_FILE)

install-dev: venv
	@echo "Installing dev requirements from $(REQUIREMENTS_FILE)..."
	@$(VENV_DIR)/bin/pip install -r requirements.txt requirements-dev.txt

precommit-setup:
	@echo "Installing pre-commit..."
	@$(VENV_DIR)/bin/pip install pre-commit
	@if [ -f $(PRECOMMIT_CONFIG) ]; then \
		echo "Installing pre-commit hooks..."; \
		$(VENV_DIR)/bin/pre-commit install; \
	else \
		echo "$(PRECOMMIT_CONFIG) not found. Please create one."; \
	fi

precommit:
	@echo "Running pre-commit on all files..."
	@pre-commit run --all-files -v

fmt:
	@echo "Running ruff format..."
	@ruff format .

# TODO: remove --exit-zero, so that it fails if there are any issues
check:
	@echo "Running ruff check..."
	@ruff check --exit-zero --output-format full --config $(RUFF_CONFIG) .
	@ruff check --exit-zero --output-format json -o .ruff_report.json --config $(RUFF_CONFIG) .

test:
	@echo "Running tests..."
	@pytest -v tests