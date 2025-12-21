# Dex Python SDK Makefile
# https://github.com/domfahey/dex-python

.DEFAULT_GOAL := help

# =============================================================================
# DEVELOPMENT
# =============================================================================

.PHONY: install
install: ## Set up development environment
	uv venv && uv sync --all-extras --dev

.PHONY: doctor
doctor: ## Verify environment and dependencies
	@echo "=== Environment Check ==="
	@uv --version
	@uv run python -c "import sys; print('python:', sys.version.split()[0])"
	@uv run python -c "import importlib.util; req=['httpx','pydantic','pydantic_settings','jellyfish','networkx','rich']; missing=[r for r in req if importlib.util.find_spec(r) is None]; print('missing deps:', ', '.join(missing) if missing else 'none')"
	@uv run python -c "import os; print('DEX_API_KEY:', 'set' if os.getenv('DEX_API_KEY') else 'missing')"

.PHONY: clean
clean: ## Remove build artifacts and caches
	rm -rf .pytest_cache .mypy_cache .ruff_cache __pycache__
	rm -rf src/**/__pycache__ tests/__pycache__ scripts/__pycache__
	rm -rf *.egg-info build/ dist/

# =============================================================================
# CODE QUALITY
# =============================================================================

.PHONY: format
format: ## Auto-fix code formatting
	uv run ruff check . --fix
	uv run ruff format .

.PHONY: lint
lint: ## Check code style
	uv run ruff check .

.PHONY: type
type: ## Run type checking
	uv run mypy src/ --strict

.PHONY: check
check: format lint type test ## Run all checks (format, lint, type, test)

# =============================================================================
# TESTING
# =============================================================================

.PHONY: test
test: ## Run all tests (excludes integration)
	uv run pytest -v

.PHONY: test-unit
test-unit: ## Run unit tests only
	uv run pytest tests/unit -v

.PHONY: test-integration
test-integration: ## Run integration tests (requires DEX_API_KEY)
	@export $$(cat .env | xargs) && uv run pytest tests/integration -m integration -v

.PHONY: test-cov
test-cov: ## Run tests with coverage report
	uv run pytest --cov=src/dex_python --cov-report=html --cov-report=term

# =============================================================================
# SYNC OPERATIONS
# =============================================================================

.PHONY: sync
sync: ## Sync contacts from Dex API to local database
	uv run python scripts/sync_with_integrity.py

.PHONY: sync-back-preview
sync-back-preview: ## Preview sync-back changes (MODE=notes|description|job_title)
	@echo "Usage: make sync-back-preview MODE=notes"
	uv run python scripts/sync_enrichment_back.py --mode $(MODE) --dry-run

.PHONY: sync-back-notes
sync-back-notes: ## Push enrichments as timeline notes
	uv run python scripts/sync_enrichment_back.py --mode notes

.PHONY: sync-back-desc
sync-back-desc: ## Push enrichments to description field
	uv run python scripts/sync_enrichment_back.py --mode description

.PHONY: sync-back-title
sync-back-title: ## Push enrichments to job_title field
	uv run python scripts/sync_enrichment_back.py --mode job_title

# =============================================================================
# DEDUPLICATION
# =============================================================================

.PHONY: analyze
analyze: ## Generate duplicate analysis report
	uv run python scripts/analyze_duplicates.py

.PHONY: flag-duplicates
flag-duplicates: ## Flag duplicate candidates in database
	uv run python scripts/flag_duplicates.py

.PHONY: resolve-duplicates
resolve-duplicates: ## Merge confirmed duplicates (destructive)
	uv run python scripts/resolve_duplicates.py

# =============================================================================
# HELP
# =============================================================================

.PHONY: help
help: ## Show this help message
	@echo "Dex Python SDK - Available Commands"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "Examples:"
	@echo "  make install          # Set up development environment"
	@echo "  make check            # Run all quality checks"
	@echo "  make sync             # Sync contacts from Dex API"
	@echo "  make analyze          # Analyze duplicates"
