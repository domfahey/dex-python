.PHONY: install test test-unit test-integration lint format type check sync doctor clean

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

sync:
	uv run python sync_with_integrity.py

doctor:
	@uv --version
	@uv run python -c "import importlib.util, os, sys; req=['httpx','pydantic','pydantic_settings','jellyfish','networkx','rich']; missing=[r for r in req if importlib.util.find_spec(r) is None]; print('python:', sys.version.split()[0]); print('missing deps:', ', '.join(missing) if missing else 'none'); print('DEX_API_KEY:', 'set' if os.getenv('DEX_API_KEY') else 'missing'); print('DEX_BASE_URL:', os.getenv('DEX_BASE_URL', 'default')); sys.exit(1 if missing else 0)"

clean:
	rm -rf .pytest_cache .venv __pycache__ src/**/__pycache__ tests/__pycache__
