# Contributing to Dex Import

Thank you for your interest in contributing to Dex Import! We welcome contributions from the community to help improve this project.

## Getting Started

1.  **Fork the repository** on GitHub.
2.  **Clone your fork** locally:
    ```bash
    git clone https://github.com/YOUR_USERNAME/dex-python.git
    cd dex-python
    ```
3.  **Install dependencies** using `uv` and `make`:
    ```bash
    make install
    ```
4.  **Verify your environment**:
    ```bash
    make doctor
    ```

## Development Workflow

1.  Create a new branch for your feature or bugfix:
    ```bash
    git checkout -b feature/my-new-feature
    ```
2.  Make your changes.
3.  **Run tests and checks** frequently:
    ```bash
    make check
    ```
    This runs formatting, linting, type checking, and unit tests. Ensure everything passes before committing.

## Pull Request Process

1.  Push your branch to your fork.
2.  Open a Pull Request (PR) against the `main` branch of the original repository.
3.  Provide a clear description of your changes, referencing any related issues.
4.  Ensure all CI checks pass.

## Coding Standards

*   **Style:** We use `ruff` for linting and formatting. Run `make format` to auto-fix issues.
*   **Types:** We use `mypy` for static type checking. All code must be strictly typed.
*   **Tests:** We use `pytest`. New features should include unit tests. Integration tests are encouraged but require a live API key.

## Reporting Issues

If you find a bug or have a feature request, please open an issue on GitHub. include:
*   Steps to reproduce.
*   Expected vs. actual behavior.
*   Environment details (OS, Python version).

Thank you for contributing!