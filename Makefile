# Makefile adapted from https://github.com/python-poetry/poetry/blob/master/Makefile

.PHONY: clean
clean:
	@rm -rf build dist .eggs *.egg-info
	@rm -rf .benchmarks .coverage coverage.xml htmlcov report.xml .tox
	@find . -type d -name '.mypy_cache' -exec rm -rf {} +
	@find . -type d -name '__pycache__' -exec rm -rf {} +
	@find . -type d -name '*pytest_cache*' -exec rm -rf {} +
	@find . -type f -name "*.py[co]" -exec rm -rf {} +

.PHONY: format
format: clean
	poetry run black pta/ tests/

.PHONY: test
test:
	@poetry run pytest -sq

.PHONY: build
build:
	@poetry build

.PHONY: tox
tox:
	@tox

.PHONY: docs
docs:
	poetry run pdoc --html -c latex_math=True --output-dir=docs/_build pta
	@mv -u docs/_build/pta/* docs/
	@rm -rf docs/_build

.PHONY: docs_clean
docs_clean:
	@rm -rf docs/*


.PHONY: check
check:
	poetry run mypy -p pta
	poetry run flake8 pta

