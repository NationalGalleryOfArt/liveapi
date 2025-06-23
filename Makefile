.PHONY: test test-verbose coverage install build clean lint format upload help

help:
	@echo "Available targets:"
	@echo "  test          - Run test suite"
	@echo "  test-verbose  - Run test suite with verbose output"
	@echo "  coverage      - Run test suite with coverage report"
	@echo "  install       - Install package in development mode"
	@echo "  build         - Build the package"
	@echo "  clean         - Clean build artifacts"
	@echo "  lint          - Run linting (if configured)"
	@echo "  format        - Format code with black"
	@echo "  upload        - Upload package to PyPI"
	@echo "  help          - Show this help message"

test:
	python -m pytest tests/ -v

test-verbose:
	python -m pytest tests/ -vv

coverage:
	python -m pytest tests/ --cov=src/automatic --cov=src/postomatic --cov-report=html --cov-report=term-missing

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