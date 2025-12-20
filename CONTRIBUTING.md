# Contributing to dex-import

Thank you for your interest in contributing!

## Development Setup

```bash
# Clone the repo
git clone https://github.com/domfahey/dex-import.git
cd dex-import

# Create virtual environment and install dependencies
uv venv
uv sync --all-extras --dev

# Run tests
uv run pytest

# Run linting
uv run ruff check .
uv run ruff format .
```

## Code Standards

- Use `ruff` for linting and formatting
- Use `mypy --strict` for type checking
- Follow PEP 8 style guidelines
- Write tests for new features (TDD preferred)
- Keep functions focused and well-documented

## Pull Request Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Make your changes with tests
4. Run `make check` to ensure all checks pass
5. Commit with clear messages following conventional commits
6. Push and open a Pull Request

## Commit Message Format

```
type: short description

Longer description if needed.
```

Types: `feat`, `fix`, `docs`, `chore`, `refactor`, `test`

## Questions?

Open an issue or contact Dominic Fahey at domfahey@gmail.com.
