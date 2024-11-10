#!make
.DEFAULT_GOAL := all

SHELL := /bin/bash -o pipefail

CURRENT_DIR := $(shell pwd)
ARCH := $(shell uname -m)

VENV_DIR := .venv
REQUIREMENTS_FILE := requirements.txt
PRECOMMIT_CONFIG := .pre-commit-config.yaml
PACKAGE_NAME = pluscoder
ENTRY_POINT = __main__.py
INSTALL_SH = install.sh
PLUSCODER_IMAGE = pluscoder:latest
PLUSCODER_FOLDER = $(HOME)/.pluscoder

DATETIME := $(shell date "+%Y-%m-%d %H:%M:%S %Z")

.PHONY: .pre-commit  ## Check that pre-commit is installed
.pre-commit:
	@pre-commit -V || echo 'Please install pre-commit: https://pre-commit.com/'

.PHONY: .ruff  ## Check that ruff is installed
.ruff:
	@ruff --version || echo 'Please install ruff: https://docs.astral.sh/ruff/installation/'

.PHONY: .pytest  ## Check that pytest is installed
.pytest:
	@pytest --version || echo 'Please install pytest: https://docs.pytest.org/en/latest/getting-started.html'

.PHONY: .docker  ## Check that docker is installed and running
.docker:
	@if ! docker version --format 'docker version: {{.Server.Version}}' > /dev/null 2>&1; then \
		echo 'Docker is not working (or is not running): https://docs.docker.com/get-docker/'; \
		exit 1; \
	fi

.PHONY: .check-pre-commit-config  ## Check that pre-commit config exists
.check-pre-commit-config:
	@if [ ! -f $(PRECOMMIT_CONFIG) ]; then \
		echo "$(PRECOMMIT_CONFIG) not found. Please create one and try again."; \
		exit 1; \
	fi

.PHONY: venv  ## Create virtual environment
venv:
	@echo [$(DATETIME)] $@
	@if [ ! -d $(VENV_DIR) ]; then \
		echo "Creating virtual environment ..."; \
		python3 -m venv $(VENV_DIR); \
	else \
		echo "Virtual environment already exists."; \
	fi

.PHONY: install  ## Install the package, dependencies, and pre-commit for local development
install: # .pre-commit
	@echo [$(DATETIME)] $@
	@echo
	pip install --upgrade --no-cache-dir pip # setuptools wheel
	@echo
	pip install --upgrade --no-cache-dir --requirement $(REQUIREMENTS_FILE)
	@echo
	pip install --editable .
	@echo
	pre-commit install --install-hooks
	@echo
	@echo "[$(DATETIME)] Done."

.PHONY: pip-install ## Install requirements
pip-install:
	@echo [$(DATETIME)] $@
	@echo "[$(DATETIME)] Installing requirements from $(REQUIREMENTS_FILE) ..."
	@pip install --requirement $(REQUIREMENTS_FILE)

.PHONY: pip-editable ## Install package in editable mode
pip-editable:
	@echo [$(DATETIME)] $@
	@echo "[$(DATETIME)] Installing package in editable mode ..."
	@pip install --editable .
# TODO: add requirements-dev and requirements-test ("[dev, test]")

.PHONY: start ## Start PlusCoder
start:
	@echo [$(DATETIME)] $@
	@echo "[$(DATETIME)] Make sure you are in the virtual environment."
	@echo "[$(DATETIME)] Starting PlusCoder ..."
	@python3.12 -m ${PACKAGE_NAME} --auto_commits f

.PHONY: test  ## Run tests
test: .pytest
	@echo [$(DATETIME)] $@
	@echo "[$(DATETIME)] Running tests ..."
	@pytest -v tests

.PHONY: lint  ## Check that source code meets quality standards
lint: .ruff
	@echo [$(DATETIME)] $@
	@ruff check . # linter
	@ruff format --check . # formatter

.PHONY: format  ## Format source code automatically
format: .ruff
	@echo [$(DATETIME)] $@
	@echo "[$(DATETIME)] Running ruff ..."
	@ruff check . --fix # linter
	@ruff format . # formatter

.PHONY: pre-commit-install  ## Install pre-commit hooks
pre-commit-install: .check-pre-commit-config .pre-commit
	@echo [$(DATETIME)] $@
	@echo "[$(DATETIME)] Installing pre-commit ..."
	@pip install --no-cache-dir pre-commit || echo 'Failed to install pre-commit. Please check your Python and pip installations.'
	@echo "[$(DATETIME)] Installing pre-commit hooks ..."
	@pre-commit install --install-hooks

.PHONY: pre-commit ## Run pre-commit hooks
pre-commit:
	@echo [$(DATETIME)] $@
	@echo "[$(DATETIME)] Running pre-commit on all files ..."
	@pre-commit run --all-files

.PHONY: build ## Build the package
build:
	@echo [$(DATETIME)] $@
	@echo "[$(DATETIME)] Building package ..."
	@pyinstaller --onefile \
		--add-data $(PACKAGE_NAME)/assets:assets \
		--name $(PACKAGE_NAME) \
		$(PACKAGE_NAME)/$(ENTRY_POINT)
	@echo "[$(DATETIME)] Done."

.PHONY: clean ## Clear local caches and build artifacts
clean:
	@echo [$(DATETIME)] $@
	rm -rf `find . -name __pycache__`
	rm -f `find . -type f -name '*.py[co]'`
	rm -f `find . -type f -name '*~'`
	rm -f `find . -type f -name '.*~'`
	rm -rf .cache
	rm -rf .pytest_cache
	rm -rf .ruff_cache
	rm -rf *.egg-info
	rm -f .coverage
	rm -f .coverage.*
	rm -rf build
	rm -rf dist
	rm -rf coverage.xml

.PHONY: clean-remote-branches ## Remove stale remote-tracking branches and references
clean-remote-branches:
	@echo [$(DATETIME)] $@
	@echo "Fetching and removing stale remote branch references..."
	@git fetch --prune
	@git remote prune origin
	@echo "Removing local branches that track deleted remote branches..."
	@git branch -vv | grep ': gone]' | awk '{print $$1}' | xargs -r git branch -D

.PHONY: docker-rmi  ## Remove the docker image (force)
docker-rmi: .docker
	@echo [$(DATETIME)] $@
	@echo "[$(DATETIME)] Removing old docker image...: ${PLUSCODER_IMAGE}"
	@docker rmi --force $(PLUSCODER_IMAGE) >/dev/null 2>&1 || true # ignore errors

# --no-cache
.PHONY: docker-build ## Build the docker image
docker-build: .docker
	@echo [$(DATETIME)] $@
	@echo "[$(DATETIME)] Building Docker image ..."
	@docker build -t $(PLUSCODER_IMAGE) .
	@echo "[$(DATETIME)] Done."

.PHONY: docker-start ## Run the docker container
docker-start: .docker
	@echo [$(DATETIME)] $@
	@echo "[$(DATETIME)] Running Docker container ...: ${PLUSCODER_IMAGE}"
	@docker run --env-file <(env) -v $(shell pwd):/app -it $(PLUSCODER_IMAGE)
	@echo "[$(DATETIME)] Done."

.PHONY: pluscoder-install ## Install PlusCoder
pluscoder-install: .docker docker-build
	@echo [$(DATETIME)] $@
	@echo "[$(DATETIME)] Installing PlusCoder ..."
	@$(SHELL) $(INSTALL_SH) -i $(PLUSCODER_IMAGE) -f $(PLUSCODER_FOLDER) -s

.PHONY: all  ## Run all checks and tests (lint, format, pre-commit, test) - this is the default target when running `make`
all: install lint format pre-commit test

.PHONY: help  ## Display this message
help:
	@grep -E \
		'^.PHONY: .*?## .*$$' $(MAKEFILE_LIST) | \
		sort | \
		awk 'BEGIN {FS = ".PHONY: |## "}; {printf "\033[36m%-30s\033[0m %s\n", $$2, $$3}'
