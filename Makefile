# Makefile adapted from https://github.com/python-poetry/poetry/blob/master/Makefile

DOCS := ./docs
DOCDST := ./_docs

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
	poetry run black pta/ tests/ pta_examples/
	poetry run autoflake --in-place --remove-all-unused-imports --ignore-init-module-imports --recursive pta/ tests/ pta_examples/

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

.PHONY: docs
docs: test
	$(MAKE) -C $(DOCS) html

.PHONY: gh-pages
gh-pages: docs
	@echo "Deleting old $(DOCDST)"
	rm -rf $(DOCDST)
	@git worktree prune && rm -rf .git/worktrees/$(shell dirname $(DOCDST))
	@mkdir -pv $(DOCDST)
	@echo "Checking out gh-pages branch into public"
	git worktree add -B gh-pages $(DOCDST) origin/gh-pages
	@echo "Copying Sphinx HTML output to $(DOCDST)"
	@cp -a $(DOCS)/_build/html/ $(DOCDST)
	@echo "Updating gh-pages branch"
	@cd $(DOCDST) && git add --all && git commit -m "Publishing docs to gh-pages"
	@echo "Pushing to origin"
	@cd $(DOCDST) && git push origin gh-pages
