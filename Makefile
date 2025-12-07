export PROJECTNAME=$(shell basename "$(PWD)")

FPS ?= 30
BASE_DIR ?= $(HOME)/Documents/Screenshots

.PHONY: $(shell grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk -F: '{print $$1}')

install: ## Install the virtual environment and install the pre-commit hooks
	@echo "🚀 Creating virtual environment using uv"
	@uv sync
	@uv run pre-commit install

check: ## Run code quality tools.
	@echo "🚀 Checking lock file consistency with 'pyproject.toml'"
	@uv lock --locked
	@echo "🚀 Linting code: Running pre-commit"
	@uv run pre-commit run -a

check-tool: ## Manually run a single pre-commit hook
	@echo "🚀 Running pre-commit hook: $(TOOL)"
	@uv run pre-commit run $(TOOL) --all-files

upgrade: ## Upgrade all dependencies to their latest versions
	@echo "🚀 Upgrading all dependencies"
	@uv lock --upgrade

test: ## Run all unit tests
	@echo "🚀 Running unit tests"
	@uv run pytest -v

test-single: ## Run a single test file (usage: make test-single TEST=test_config.py)
	@echo "🚀 Running single test: $(TEST)"
	@uv run pytest -v tests/$(TEST)

run: ## Run the application
	@echo "🚀 Running $(PROJECTNAME) viewer"
	@uv run python viewer.py

clean: ## Clean build artifacts
	@echo "🚀 Removing build artifacts"
	@find . -type f -name "*.pyc" -delete
	@find . -type d -name "__pycache__" -delete
	@find . -type d -name "*.egg-info" -delete
	@rm -rf build/ dist/

package: clean ## Build app bundle with PyInstaller
	@uv run pyinstaller main.spec --clean

install-macosx: package ## Installs application in users Application folder
	./scripts/install-macosx.sh SnapSpan.app

setup: ## One command setup
	@make install-macosx
	@echo "Installation completed"

timelapse: ## Generate a timelapse MP4 for a single date
ifndef DATE
	$(error DATE is required, e.g., make timelapse DATE=YYYY-MM-DD)
endif
	@CMD="uv run python timelapse.py --date $(DATE) --fps $(FPS) --base-dir \"$(BASE_DIR)\""; \
	if [ "$(OVERWRITE)" = "true" ]; then CMD="$$CMD --overwrite"; fi; \
	if [ "$(DELETE)" = "true" ]; then CMD="$$CMD --delete"; fi; \
	echo $$CMD; \
	$$CMD

timelapses: ## Generate timelapses for all dates under BASE_DIR
	@CMD="./scripts/generate_timelapses.sh --fps $(FPS) --base-dir \"$(BASE_DIR)\""; \
	if [ "$(OVERWRITE)" = "true" ]; then CMD="$$CMD --overwrite"; fi; \
	if [ "$(DELETE)" = "true" ]; then CMD="$$CMD --delete"; fi; \
	echo $$CMD; \
	$$CMD

.PHONY: help
.DEFAULT_GOAL := help

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'
