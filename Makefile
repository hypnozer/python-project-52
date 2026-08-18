install:
	uv sync

update:
	uv lock --upgrade
	uv sync

test:
	uv run pytest

test-coverage:
	uv run pytest --cov=task_manager --cov-report term --cov-report xml

lint:
	uv run ruff check

check: test lint

build:
	uv build

.PHONY: install update test test-coverage lint check build

