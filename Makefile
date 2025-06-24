.PHONY: test test-verbose test-ui test-all setup-playwright coverage install build clean lint format upload help

help:
	@echo "Available targets:"
	@echo "  test          - Run test suite (excluding UI tests)"
	@echo "  test-verbose  - Run test suite with verbose output"
	@echo "  test-ui       - Run UI tests with Playwright"
	@echo "  test-all      - Run all tests including UI tests"
	@echo "  setup-playwright - Install Playwright and browser drivers"
	@echo "  coverage      - Run test suite with coverage report"
	@echo "  install       - Install package in development mode"
	@echo "  build         - Build the package"
	@echo "  clean         - Clean build artifacts"
	@echo "  lint          - Run linting (if configured)"
	@echo "  format        - Format code with black"
	@echo "  upload        - Upload package to PyPI"
	@echo "  help          - Show this help message"

test:
	python -m pytest tests/ -k "not test_designer_ui.py" -v

test-verbose:
	python -m pytest tests/ -k "not test_designer_ui.py" -vv

test-ui:
	python -m pytest tests/test_designer_ui.py -v

test-all:
	python -m pytest tests/ -v

setup-playwright:
	pip install playwright
	playwright install

coverage:
	python -m pytest tests/ --cov=src/liveapi --cov-report=html --cov-report=term-missing

install:
	pip install -e .

build:
	python -m build

clean:
	rm -rf dist/
	rm -rf build/
	rm -rf *.egg-info/
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

lint:
	flake8 src/ tests/

format:
	black src/ tests/

upload:
	twine upload dist/*
