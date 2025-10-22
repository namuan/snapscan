export PROJECTNAME=$(shell basename "$(PWD)")
PY=./venv/bin/python3

FPS ?= 30
BASE_DIR ?= $(HOME)/Documents/Screenshots

.SILENT: ;               # no need for @

setup: clean ## Re-initiates virtualenv
	rm -rf venv
	python3 -m venv venv

deps: ## Install dependencies
	$(PY) -m pip install --upgrade pip
	$(PY) -m pip install --upgrade -r requirements.txt
	$(PY) -m pip install --upgrade -r requirements-dev.txt

pre-commit: ## Manually run all precommit hooks
	./venv/bin/pre-commit install
	./venv/bin/pre-commit run --all-files

pre-commit-tool: ## Manually run a single pre-commit hook
	./venv/bin/pre-commit run $(TOOL) --all-files

clean: ## Clean package
	find . -type d -name '__pycache__' | xargs rm -rf
	rm -rf build dist

package: pre-commit ## Build app bundle with PyInstaller
	./venv/bin/pyinstaller main.spec

install-macosx: package ## Installs application in users Application folder
	./scripts/install-macosx.sh SnapSpan.app

timelapse: ## Generate a timelapse MP4 for a single date
ifndef DATE
	$(error DATE is required, e.g., make timelapse DATE=YYYY-MM-DD)
endif
	@CMD="$(PY) timelapse.py --date $(DATE) --fps $(FPS)"; \
	if [ "$(OVERWRITE)" = "true" ]; then CMD="$$CMD --overwrite"; fi; \
	if [ "$(DELETE)" = "true" ]; then CMD="$$CMD --delete"; fi; \
	echo $$CMD; \
	$$CMD

timelapses: ## Generate timelapses for all dates under BASE_DIR
	@CMD="./scripts/generate_timelapses.sh --fps $(FPS) --base-dir \"$(BASE_DIR)\""; \
	if [ "$(OVERWRITE)" = "true" ]; then CMD="$$CMD --overwrite"; fi; \
	if [ "$(DELETE)" = "true" ]; then CMD="$$CMD --delete"; fi; \
	if [ "$(MISSING_ONLY)" = "true" ]; then CMD="$$CMD --missing-only"; fi; \
	echo $$CMD; \
	$$CMD

.PHONY: help
.DEFAULT_GOAL := help

help: Makefile
	echo
	echo " Choose a command run in "$(PROJECTNAME)":"
	echo
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
	echo
