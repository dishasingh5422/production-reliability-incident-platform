.PHONY: install lint typecheck security test verify run

install:
	python3.11 -m pip install -e '.[dev]'

lint:
	ruff check .

typecheck:
	mypy app

security:
	bandit -q -r app

test:
	pytest --cov=app --cov-report=term-missing

verify: lint typecheck security test

run:
	uvicorn app.main:app --host 0.0.0.0 --port 8080

