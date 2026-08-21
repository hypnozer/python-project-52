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

dev:
	uv run python manage.py runserver

collectstatic:
	uv run python manage.py collectstatic --no-input

tailwind-build:
	uv run python manage.py tailwind build

migrate:
	uv run python manage.py migrate

render-start:
	gunicorn task_manager.wsgi

build:
	./build.sh

package-build:
	uv build

.PHONY: install update test test-coverage lint check dev collectstatic \
	tailwind-build migrate render-start build package-build
