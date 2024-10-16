#!make
SHELL := /bin/bash

VENV_DIR := .venv
REQUIREMENTS_FILE := requirements.txt
PRECOMMIT_CONFIG := .pre-commit-config.yaml
PACKAGE_NAME = pluscoder
ENTRY_POINT = __main__.py
INSTALL_SH = install.sh
PLUSCODER_IMAGE = pluscoder:latest
PLUSCODER_FOLDER = $(HOME)/.pluscoder

.PHONY: venv install_requirements precommit install_precommit build clean start

# Local development commands
venv:
	@if [ ! -d $(VENV_DIR) ]; then \
		echo "Creating virtual environment..."; \
		python3 -m venv $(VENV_DIR); \
	else \
		echo "Virtual environment already exists."; \
	fi

pip-install:
	@echo "Installing requirements from $(REQUIREMENTS_FILE)..."
	@pip install -r $(REQUIREMENTS_FILE)

pip-editable:
	@echo "Installing package in editable mode..."
	@pip install -e .
	# TODO add requirements-dev and requirements-test ("[dev, test]")

start:
	@echo "Make sure you are in the virtual environment."
	@echo "Starting PlusCoder..."
	@python3.12 -m $PACKAGE_NAME --auto_commits f

test:
	@echo "Running tests..."
	@pytest -v tests

format:
	@echo "Running ruff..."
	@ruff format .

# Pre-commit commands
precommit-install:
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


# Build the package
build:
	@echo "Building package..."
	@pyinstaller --onefile \
		--add-data $(PACKAGE_NAME)/assets:assets \
		--name $(PACKAGE_NAME) \
		$(PACKAGE_NAME)/$(ENTRY_POINT)

clean:
	@rm -rf dist build __pycache__


# Docker commands
docker-build:
	@echo "Building Docker image..."
	@docker build -t $(PLUSCODER_IMAGE) .

docker-start:
	@echo "Running Docker container..."
	@docker run --env-file <(env) -v $(shell pwd):/app -it $(PLUSCODER_IMAGE)

# PlusCoder installer
pluscoder-install: docker-build
	@echo "Installing PlusCoder..."
	@$(SHELL) $(INSTALL_SH) -i $(PLUSCODER_IMAGE) -f $(PLUSCODER_FOLDER) -s
