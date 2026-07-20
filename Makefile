.PHONY: install dev lint lint-fix format format-check test test-cov clean build

install:
	pip install -e .

dev:
	pip install -e ".[dev,yaml,excel,dotenv,pydantic]"

lint:
	ruff check .
	mypy --strict behave_kit/

lint-fix:
	ruff check . --fix

format:
	ruff format .

format-check:
	ruff format --check .

test:
	pytest tests/ -v

test-cov:
	pytest tests/ -v --cov --cov-report=term-missing --cov-fail-under=90

clean:
	rm -rf dist/ build/ *.egg-info/ .coverage htmlcov/ .pytest_cache/ .ruff_cache/ .mypy_cache/

build:
	python -m build
