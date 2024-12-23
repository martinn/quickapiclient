.PHONY: install
install: ## Install the uv environment and install the pre-commit hooks
	@echo "🚀 Creating virtual environment using uv"
	@uv sync
	@uvx pre-commit install

.PHONY: check
check: ## Run code quality tools.
	@echo "🚀 Checking uv lock file consistency with 'pyproject.toml': Running uv lock --check"
	@uv lock --check
	@echo "🚀 Linting code: Running pre-commit"
	@uv run --group dev pre-commit run -a
	@echo "🚀 Static type checking: Running mypy"
	@uv run --group dev mypy
	@echo "🚀 Checking for obsolete dependencies: Running deptry"
	@uv run --group dev deptry .

.PHONY: test
test: ## Test the code with pytest
	@echo "🚀 Testing code: Running pytest"
	@uv run --group dev pytest --cov --cov-config=pyproject.toml --cov-report=xml

.PHONY: build
build: clean-build ## Build wheel file using uv
	@echo "🚀 Creating wheel file"
	@uv build

.PHONY: clean-build
clean-build: ## clean build artifacts
	@rm -rf dist

.PHONY: publish
publish: ## publish a release to pypi.
	@echo "🚀 Publishing."
	@uv publish --token $(PYPI_TOKEN)

.PHONY: build-and-publish
build-and-publish: build publish ## Build and publish.

.PHONY: docs-test
docs-test: ## Test if documentation can be built without warnings or errors
	@uv run --group docs mkdocs build -s

.PHONY: docs
docs: ## Build and serve the documentation
	@uv run --group docs mkdocs serve

.PHONY: help
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help
