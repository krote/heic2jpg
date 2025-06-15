.PHONY: test test-unit test-integration test-coverage clean install help

# Default target
help:
	@echo "Available targets:"
	@echo "  install        - Install dependencies"
	@echo "  test           - Run all tests"
	@echo "  test-unit      - Run unit tests only"
	@echo "  test-integration - Run integration tests only"
	@echo "  test-coverage  - Run tests with coverage report"
	@echo "  clean          - Clean up generated files"

install:
	pip install -r requirements.txt

test:
	pytest

test-unit:
	pytest -m "not integration"

test-integration:
	pytest -m integration

test-coverage:
	pytest --cov=heic2jpg --cov-report=html --cov-report=term

clean:
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf __pycache__/
	rm -rf tests/__pycache__/
	find . -name "*.pyc" -delete
	find . -name "*.pyo" -delete