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
VENV_DIR := .venv
BIN_DIR := $(VENV_DIR)/bin
ENV_FILE ?= .env
ENV_EXAMPLE_FILE ?= .env.example
PACKAGE_DIR ?= src/dex_python
DATA_DIR ?= output
DB_PATH ?= $(DATA_DIR)/dex_contacts.db
REPORT_PATH ?= $(DATA_DIR)/DUPLICATE_REPORT.md
UV_SYNC_ARGS ?= --all-extras --dev
PYTEST_ARGS ?=
RUFF_CHECK_ARGS ?=
RUFF_FORMAT_ARGS ?=
MYPY_ARGS ?= --strict
SYNC_BACK_ARGS ?=
DOCTOR_API_LIMIT ?= 1
FORCE ?= 0
PYTHON := $(BIN_DIR)/python
PYTEST := $(BIN_DIR)/pytest
RUFF := $(BIN_DIR)/ruff
MYPY := $(BIN_DIR)/mypy

# Colors
CYAN := \033[36m
GREEN := \033[32m
YELLOW := \033[33m
RESET := \033[0m

LOAD_ENV = set -a; if [ -f "$(ENV_FILE)" ]; then source "$(ENV_FILE)"; fi; set +a;
RUN_WITH_ENV = $(LOAD_ENV) DEX_DATA_DIR="$(DATA_DIR)"

define run_sync_back
	@mkdir -p "$(dir $(DB_PATH))"
	@$(RUN_WITH_ENV) $(PYTHON) scripts/sync_enrichment_back.py --db "$(DB_PATH)" --mode "$(1)" $(2) $(SYNC_BACK_ARGS)
endef

# Declare all phony targets
.PHONY: bootstrap install doctor doctor-api clean clean-venv distclean \
        format format-check lint type check \
        test test-unit test-integration test-cov \
        sync sync-back-preview sync-back-notes sync-back-desc sync-back-title \
        analyze flag-duplicates review-duplicates resolve-duplicates \
        _require-api-key _require-force _require-venv \
        help

# =============================================================================
# DEVELOPMENT
# =============================================================================

bootstrap: install ## Initialize local config and data directories
	@mkdir -p "$(dir $(ENV_FILE))" "$(dir $(DB_PATH))" "$(dir $(REPORT_PATH))"
	@if [ -f "$(ENV_FILE)" ]; then \
		echo -e "$(GREEN)✓ Using existing $(ENV_FILE)$(RESET)"; \
	elif [ -f "$(ENV_EXAMPLE_FILE)" ]; then \
		cp "$(ENV_EXAMPLE_FILE)" "$(ENV_FILE)"; \
		echo -e "$(GREEN)✓ Created $(ENV_FILE) from $(ENV_EXAMPLE_FILE)$(RESET)"; \
	else \
		echo -e "$(YELLOW)! $(ENV_EXAMPLE_FILE) not found; skipping env bootstrap$(RESET)"; \
	fi
	@echo "Next steps:"
	@echo "  1. Edit $(ENV_FILE) and set DEX_API_KEY"
	@echo "  2. Run make doctor"
	@echo "  3. Run make doctor-api"

install: ## Set up development environment
	@if [ ! -d "$(VENV_DIR)" ]; then \
		echo "Creating virtual environment at $(VENV_DIR)"; \
		$(UV) venv "$(VENV_DIR)"; \
	else \
		echo "Using existing virtual environment at $(VENV_DIR)"; \
	fi
	@$(UV) sync $(UV_SYNC_ARGS)
	@echo -e "$(GREEN)✓ Environment ready$(RESET)"

doctor: _require-venv ## Verify local environment and dependencies
	@echo "=== Offline Environment Check ==="
	@$(UV) --version
	@$(PYTHON) -c "import sys; print('python:', sys.version.split()[0]); print('python executable:', sys.executable)"
	@$(PYTHON) -c "import importlib.util; req=['httpx','pydantic','pydantic_settings','jellyfish','networkx','rich','unidecode']; missing=[r for r in req if importlib.util.find_spec(r) is None]; print('missing deps:', ', '.join(missing) if missing else 'none')"
	@if [ -f "$(ENV_FILE)" ]; then echo "env file: present ($(ENV_FILE))"; else echo "env file: missing ($(ENV_FILE))"; fi
	@echo "VENV_DIR: $(VENV_DIR)"
	@echo "DATA_DIR: $(DATA_DIR)"
	@echo "DB_PATH: $(DB_PATH)"
	@$(LOAD_ENV) $(PYTHON) -c "import os; print('DEX_API_KEY:', 'set' if os.getenv('DEX_API_KEY') else 'missing')"

doctor-api: _require-venv _require-api-key ## Verify Dex API authentication and connectivity
	@echo "=== Dex API Check ==="
	@$(RUN_WITH_ENV) $(PYTHON) -c "import os; from dex_python import DexClient; base_url=os.getenv('DEX_BASE_URL', 'https://api.getdex.com/api/rest'); client=DexClient(); contacts=client.get_contacts(limit=$(DOCTOR_API_LIMIT)); client.close(); print('base_url:', base_url); print('api auth: ok'); print('sample contacts fetched:', len(contacts))"

clean: ## Remove build artifacts and caches
	@rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@rm -rf *.egg-info build/ dist/ .coverage .coverage.*
	@echo -e "$(GREEN)✓ Cleaned$(RESET)"

clean-venv: ## Remove the local virtual environment
	@rm -rf "$(VENV_DIR)"
	@echo -e "$(GREEN)✓ Removed $(VENV_DIR)$(RESET)"

distclean: clean clean-venv ## Remove build artifacts and virtual environment
	@echo -e "$(GREEN)✓ Distclean complete$(RESET)"

# =============================================================================
# CODE QUALITY
# =============================================================================

format: _require-venv ## Auto-fix code formatting
	@$(RUFF) check . --fix --quiet $(RUFF_CHECK_ARGS)
	@$(RUFF) format . --quiet $(RUFF_FORMAT_ARGS)
	@echo -e "$(GREEN)✓ Formatted$(RESET)"

format-check: _require-venv ## Check formatting without modifying files
	@$(RUFF) format . --check $(RUFF_FORMAT_ARGS)

lint: _require-venv ## Check code style
	@$(RUFF) check . $(RUFF_CHECK_ARGS)

type: _require-venv ## Run type checking
	@$(MYPY) $(PACKAGE_DIR) $(MYPY_ARGS)

check: format-check lint type test ## Run all checks (format check, lint, type, test)
	@echo -e "$(GREEN)✓ All checks passed$(RESET)"

# =============================================================================
# TESTING
# =============================================================================

test: _require-venv ## Run all tests (excludes integration)
	@$(PYTEST) $(PYTEST_ARGS) -v

test-unit: _require-venv ## Run unit tests only
	@$(PYTEST) $(PYTEST_ARGS) tests/unit -v

test-integration: _require-venv _require-api-key ## Run integration tests (requires DEX_API_KEY)
	@$(RUN_WITH_ENV) $(PYTEST) $(PYTEST_ARGS) tests/integration -m integration -v

test-cov: _require-venv ## Run tests with coverage report
	@$(PYTEST) $(PYTEST_ARGS) --cov=$(PACKAGE_DIR) --cov-report=html --cov-report=term
	@echo -e "$(GREEN)✓ Coverage report: htmlcov/index.html$(RESET)"

# =============================================================================
# SYNC OPERATIONS
# =============================================================================

sync: _require-venv _require-api-key ## Sync contacts from Dex API to local database
	@mkdir -p "$(DATA_DIR)"
	@$(RUN_WITH_ENV) $(PYTHON) scripts/sync_with_integrity.py

sync-back-preview: _require-venv ## Preview sync-back changes (MODE=notes|description|job_title)
	@if [ -z "$(MODE)" ]; then \
		echo -e "$(YELLOW)Usage: make sync-back-preview MODE=notes$(RESET)"; \
		exit 1; \
	fi
	$(call run_sync_back,$(MODE),--dry-run)

sync-back-notes: _require-venv _require-api-key ## Push enrichments as timeline notes
	$(call run_sync_back,notes,)

sync-back-desc: _require-venv _require-api-key ## Push enrichments to description field
	$(call run_sync_back,description,)

sync-back-title: _require-venv _require-api-key ## Push enrichments to job_title field
	$(call run_sync_back,job_title,)

# =============================================================================
# DEDUPLICATION
# =============================================================================

analyze: _require-venv ## Generate duplicate analysis report
	@mkdir -p "$(dir $(REPORT_PATH))"
	@$(RUN_WITH_ENV) $(PYTHON) scripts/analyze_duplicates.py --db "$(DB_PATH)" --output "$(REPORT_PATH)"

flag-duplicates: _require-venv ## Flag duplicate candidates in database
	@mkdir -p "$(dir $(DB_PATH))"
	@$(RUN_WITH_ENV) $(PYTHON) scripts/flag_duplicates.py --db "$(DB_PATH)"

review-duplicates: _require-venv ## Interactively review duplicate candidates
	@mkdir -p "$(dir $(DB_PATH))"
	@$(RUN_WITH_ENV) $(PYTHON) scripts/review_duplicates.py --db "$(DB_PATH)"

resolve-duplicates: _require-venv _require-force ## Merge confirmed duplicates (destructive; requires FORCE=1)
	@mkdir -p "$(dir $(DB_PATH))"
	@$(RUN_WITH_ENV) $(PYTHON) scripts/resolve_duplicates.py --db "$(DB_PATH)"

_require-api-key:
	@$(LOAD_ENV) if [ -z "$$DEX_API_KEY" ]; then \
		echo -e "$(YELLOW)DEX_API_KEY is missing. Set it in $(ENV_FILE) or export it in your shell.$(RESET)"; \
		exit 1; \
	fi

_require-force:
	@if [ "$(FORCE)" != "1" ]; then \
		echo -e "$(YELLOW)This target is destructive. Re-run with FORCE=1 to confirm.$(RESET)"; \
		exit 1; \
	fi

_require-venv:
	@if [ ! -x "$(PYTHON)" ]; then \
		echo -e "$(YELLOW)Virtual environment not found at $(VENV_DIR). Run 'make install' first.$(RESET)"; \
		exit 1; \
	fi

# =============================================================================
# HELP
# =============================================================================

print-%: ## Print the value of a Make variable
	@printf '%s=%s\n' '$*' '$($*)'

help: ## Show this help message
	@echo -e "$(CYAN)Dex Python SDK$(RESET) - Available Commands"
	@echo ""
	@grep -E '^[a-zA-Z0-9_.%/-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  $(CYAN)%-22s$(RESET) %s\n", $$1, $$2}'
	@echo ""
	@echo "Examples:"
	@echo "  make bootstrap            # Set up the project and create local config"
	@echo "  make install              # Set up development environment"
	@echo "  make doctor               # Run offline environment checks"
	@echo "  make doctor-api           # Verify live API auth"
	@echo "  make check                # Run all quality checks"
	@echo "  make format               # Auto-fix formatting"
	@echo "  make sync                 # Sync contacts from Dex API"
	@echo "  make resolve-duplicates FORCE=1  # Merge confirmed duplicates"
