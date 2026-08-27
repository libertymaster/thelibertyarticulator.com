SHELL := /bin/sh
PYTHON ?= python3
VENV ?= .venv
BIN := $(VENV)/bin

.PHONY: install migrate run worker beat test coverage lint format check collectstatic seed shell

install:
	$(PYTHON) -m venv $(VENV)
	$(BIN)/python -m pip install --upgrade pip
	$(BIN)/python -m pip install -e '.[dev]'

migrate:
	$(BIN)/python manage.py migrate

run:
	$(BIN)/python manage.py runserver 0.0.0.0:8000

worker:
	$(BIN)/celery -A config worker -l info

beat:
	$(BIN)/celery -A config beat -l info

test:
	$(BIN)/pytest

coverage:
	$(BIN)/coverage run -m pytest
	$(BIN)/coverage report

lint:
	$(BIN)/ruff check .
	$(BIN)/ruff format --check .

format:
	$(BIN)/ruff check --fix .
	$(BIN)/ruff format .

check: lint test
	DJANGO_SETTINGS_MODULE=config.settings.production \
	DJANGO_SECRET_KEY=check-only-secret-key-with-sufficient-length-for-deploy-checks \
	DATABASE_URL=sqlite:///check.sqlite3 \
	ALLOWED_HOSTS=example.com \
	$(BIN)/python manage.py check --deploy

collectstatic:
	$(BIN)/python manage.py collectstatic --noinput

seed:
	$(BIN)/python manage.py seed_demo

shell:
	$(BIN)/python manage.py shell
