.PHONY: install test test-unit test-integration lint format type check clean

install:
	uv venv && uv sync --all-extras --dev

test:
	uv run pytest -v

test-unit:
	uv run pytest tests/unit -v

test-integration:
	@export $$(cat .env | xargs) && uv run pytest tests/integration -m integration -v

lint:
	uv run ruff check .

format:
	uv run ruff check . --fix
	uv run ruff format .

type:
	uv run mypy src/ --strict

check: format lint type test

clean:
	rm -rf .pytest_cache .venv __pycache__ src/**/__pycache__ tests/__pycache__
