# Dex Python SDK Makefile
# https://github.com/domfahey/dex-python

SHELL := /bin/bash
.DEFAULT_GOAL := help
.SHELLFLAGS := -eu -o pipefail -c
MAKEFLAGS += --no-builtin-rules --no-print-directory

.SUFFIXES:
.DELETE_ON_ERROR:

# Variables
UV ?= uv
ENV_FILE ?= .env
PACKAGE_DIR := src/dex_python
PYTHON := $(UV) run python
PYTEST := $(UV) run pytest
RUFF := $(UV) run ruff
MYPY := $(UV) run mypy

# Colors
CYAN := \033[36m
GREEN := \033[32m
YELLOW := \033[33m
RESET := \033[0m

define load_env
set -a; \
if [ -f "$(ENV_FILE)" ]; then source "$(ENV_FILE)"; fi; \
set +a;
endef

# Declare all phony targets
.PHONY: install doctor clean format format-check lint type check \
        test test-unit test-integration test-cov \
        sync sync-back-preview sync-back-notes sync-back-desc sync-back-title \
        analyze flag-duplicates review-duplicates resolve-duplicates \
        _require-api-key \
        help

# =============================================================================
# DEVELOPMENT
# =============================================================================

install: ## Set up development environment
	@$(UV) venv
	@$(UV) sync --all-extras --dev
	@echo -e "$(GREEN)✓ Environment ready$(RESET)"

doctor: ## Verify environment and dependencies
	@echo "=== Environment Check ==="
	@$(UV) --version
	@$(PYTHON) -c "import sys; print('python:', sys.version.split()[0])"
	@$(PYTHON) -c "import importlib.util; req=['httpx','pydantic','pydantic_settings','jellyfish','networkx','rich','unidecode']; missing=[r for r in req if importlib.util.find_spec(r) is None]; print('missing deps:', ', '.join(missing) if missing else 'none')"
	@$(load_env) $(PYTHON) -c "import os; print('DEX_API_KEY:', 'set' if os.getenv('DEX_API_KEY') else 'missing')"

clean: ## Remove build artifacts and caches
	@rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@rm -rf *.egg-info build/ dist/ .coverage
	@echo -e "$(GREEN)✓ Cleaned$(RESET)"

# =============================================================================
# CODE QUALITY
# =============================================================================

format: ## Auto-fix code formatting
	@$(RUFF) check . --fix --quiet
	@$(RUFF) format . --quiet
	@echo -e "$(GREEN)✓ Formatted$(RESET)"

format-check: ## Check formatting without modifying files
	@$(RUFF) format . --check

lint: ## Check code style
	@$(RUFF) check .

type: ## Run type checking
	@$(MYPY) $(PACKAGE_DIR) --strict

check: format-check lint type test ## Run all checks (format check, lint, type, test)
	@echo -e "$(GREEN)✓ All checks passed$(RESET)"

# =============================================================================
# TESTING
# =============================================================================

test: ## Run all tests (excludes integration)
	@$(PYTEST) -v

test-unit: ## Run unit tests only
	@$(PYTEST) tests/unit -v

test-integration: _require-api-key ## Run integration tests (requires DEX_API_KEY)
	@$(load_env) $(PYTEST) tests/integration -m integration -v

test-cov: ## Run tests with coverage report
	@$(PYTEST) --cov=$(PACKAGE_DIR) --cov-report=html --cov-report=term
	@echo -e "$(GREEN)✓ Coverage report: htmlcov/index.html$(RESET)"

# =============================================================================
# SYNC OPERATIONS
# =============================================================================

sync: _require-api-key ## Sync contacts from Dex API to local database
	@$(load_env) $(PYTHON) scripts/sync_with_integrity.py

sync-back-preview: _require-api-key ## Preview sync-back changes (MODE=notes|description|job_title)
	@if [ -z "$(MODE)" ]; then \
		echo -e "$(YELLOW)Usage: make sync-back-preview MODE=notes$(RESET)"; \
		exit 1; \
	fi
	@$(load_env) $(PYTHON) scripts/sync_enrichment_back.py --mode "$(MODE)" --dry-run

sync-back-notes: _require-api-key ## Push enrichments as timeline notes
	@$(load_env) $(PYTHON) scripts/sync_enrichment_back.py --mode notes

sync-back-desc: _require-api-key ## Push enrichments to description field
	@$(load_env) $(PYTHON) scripts/sync_enrichment_back.py --mode description

sync-back-title: _require-api-key ## Push enrichments to job_title field
	@$(load_env) $(PYTHON) scripts/sync_enrichment_back.py --mode job_title

# =============================================================================
# DEDUPLICATION
# =============================================================================

analyze: ## Generate duplicate analysis report
	@DEX_DATA_DIR=. $(PYTHON) scripts/analyze_duplicates.py

flag-duplicates: ## Flag duplicate candidates in database
	@DEX_DATA_DIR=. $(PYTHON) scripts/flag_duplicates.py

review-duplicates: ## Interactively review duplicate candidates
	@DEX_DATA_DIR=. $(PYTHON) scripts/review_duplicates.py

resolve-duplicates: ## Merge confirmed duplicates (destructive)
	@DEX_DATA_DIR=. $(PYTHON) scripts/resolve_duplicates.py

_require-api-key:
	@$(load_env) if [ -z "$$DEX_API_KEY" ]; then \
		echo -e "$(YELLOW)DEX_API_KEY is missing. Set it in $(ENV_FILE) or export it in your shell.$(RESET)"; \
		exit 1; \
	fi

# =============================================================================
# HELP
# =============================================================================

help: ## Show this help message
	@echo -e "$(CYAN)Dex Python SDK$(RESET) - Available Commands"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  $(CYAN)%-22s$(RESET) %s\n", $$1, $$2}'
	@echo ""
	@echo "Examples:"
	@echo "  make install              # Set up development environment"
	@echo "  make check                # Run all quality checks"
	@echo "  make format               # Auto-fix formatting"
	@echo "  make sync                 # Sync contacts from Dex API"
	@echo "  make analyze              # Analyze duplicates"
	@echo "  make review-duplicates    # Review duplicates interactively"
