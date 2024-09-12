export PROJECTNAME=$(shell basename "$(PWD)")
PY=./venv/bin/python3

.SILENT: ;               # no need for @

deps: ## Install dependencies
	$(PY) -m pip install --upgrade -r requirements.txt
	$(PY) -m pip install --upgrade pip

lint: ## Run black for code formatting
	black . --exclude venv

clean: ## Clean package
	find . -type d -name '__pycache__' | xargs rm -rf
	rm -rf build dist

package: ## Run installer
	pyinstaller main.spec

.PHONY: help
.DEFAULT_GOAL := help

help: Makefile
	echo
	echo " Choose a command run in "$(PROJECTNAME)":"
	echo
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
	echo