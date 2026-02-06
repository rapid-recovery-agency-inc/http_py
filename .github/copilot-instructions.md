# HTTPpy shared library

This repository contains the shared library code HTTP APis and Microservices.

### Frequently Used Commands
```bash
# Quick development cycle
poetry install
poetry run ruff format .
poetry run ruff check --fix .
poetry run python main.py

# Full validation
poetry run ruff check .
poetry run mypy shared --ignore-missing-imports
poetry run pre-commit run --all-files

# Dependency management
poetry add <package>
poetry remove <package>
poetry update
```