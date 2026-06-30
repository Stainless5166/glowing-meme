.PHONY: dev test fmt build-packages clean

PYTHON := python3

VENV := .venv

UV := uv

dev:
	$(UV) sync --all-extras

test:
	$(UV) run pytest

fmt:
	$(UV) run black src tests agent

build-packages:
	./scripts/build_packages.sh

clean:
	rm -rf dist build .pytest_cache .mypy_cache .ruff_cache
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	find . -type d -name '*.egg-info' -prune -exec rm -rf {} +
