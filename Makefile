.PHONY: help install run test clean format lint

help:
	@echo "APGI REST API - Available commands:"
	@echo "  make install    - Install dependencies"
	@echo "  make run        - Run the API server"
	@echo "  make test       - Run tests"
	@echo "  make clean      - Clean up generated files"
	@echo "  make format     - Format code with black and isort"
	@echo "  make lint       - Run linting checks"

install:
	pip install -r requirements.txt

run:
	uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

test:
	pytest tests/ -v

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +
	find . -type f -name ".coverage" -delete

format:
	black api/
	isort api/

lint:
	flake8 api/
	mypy api/
