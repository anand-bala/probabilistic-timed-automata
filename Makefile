# Makefile adapted from https://github.com/python-poetry/poetry/blob/master/Makefile

DOCS := ./docs

.PHONY: clean clean_py clean_docs
clean_py:
	@echo "Cleaning Python package artifacts"
	@rm -rf build dist .eggs *.egg-info
	@rm -rf .benchmarks .coverage coverage.xml htmlcov report.xml .tox
	@find . -type d -name '.mypy_cache' -exec rm -rf {} +
	@find . -type d -name '__pycache__' -exec rm -rf {} +
	@find . -type d -name '*pytest_cache*' -exec rm -rf {} +
	@find . -type f -name "*.py[co]" -exec rm -rf {} +

clean_docs:
	@echo "Removing Sphinx build tree"
	@$(MAKE) -C $(DOCS) clean

clean: clean_docs clean_py


.PHONY: format
format: clean_py
	poetry run black pta/ tests/
	poetry run autoflake --in-place --remove-all-unused-imports --ignore-init-module-imports --recursive pta/ tests/

.PHONY: check
check:
	poetry run mypy -p pta
	poetry run flake8 pta

.PHONY: test
test: check
	@poetry run pytest

.PHONY: build docs
build: format docs
	@poetry build

docs:
	$(MAKE) -C $(DOCS) html
	@echo "Copying built docs to $(DOCS)"
	@mkdir -p $(DOCS)
	@cp -a $(DOCS)/_build/html/. $(DOCS)

