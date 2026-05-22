# Contributing to PyContinuum

Thank you for your interest in contributing! We welcome all kinds of contributions: bug reports, feature requests, documentation improvements, and code.

## Getting Started
- Install the development dependencies: `pip install -e ".[dev]"`
- Run the tests: `pytest`
- Run the linters: `ruff check .` and `mypy src/`

## Pull Request Process
1. Fork the repository and create a feature branch.
2. Add or update tests for your changes.
3. Ensure `pytest` passes with 100% coverage.
4. Run `ruff check .` and `mypy src/ --strict` without errors.
5. Submit a pull request to the `main` branch.

## Code Style
- Python 3.12+ only.
- All public functions must have Google‑style docstrings.
- Type hints on all parameters and return values.
- Use `ruff format` for consistent formatting.

## Reporting Bugs
Use the bug report issue template and include:
- Python version
- PyContinuum version
- Minimal reproducible example

Thank you for helping make PyContinuum better!
