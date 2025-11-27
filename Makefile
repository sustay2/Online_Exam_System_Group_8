.PHONY: install lint test run format type ci db-up db-shell

VENV := venv
PYTHON := $(VENV)/bin/python

install:
	pip install -e ".[dev]"

lint:
	ruff check .
	black --check .
	mypy src
	pytest --maxfail=1 --disable-warnings -q

format:
	ruff check . --fix
	black .
	isort .

type:
	mypy src

test:
	pytest --cov=src --cov-report=term-missing

run:
	flask --app src/online_exam:create_app run --debug

ci: lint type test

db-up:
	sudo systemctl start mysql || true

db-shell:
	mysql -u examuser -p examdb