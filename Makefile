.PHONY: test test-verbose install build clean lint help

help:
	@echo "Available targets:"
	@echo "  test          - Run test suite"
	@echo "  test-verbose  - Run test suite with verbose output"
	@echo "  install       - Install package in development mode"
	@echo "  build         - Build the package"
	@echo "  clean         - Clean build artifacts"
	@echo "  lint          - Run linting (if configured)"
	@echo "  help          - Show this help message"

test:
	python -m pytest tests/ -v

test-verbose:
	python -m pytest tests/ -vv

install:
	pip install -e .

build:
	python -m build

clean:
	rm -rf dist/
	rm -rf build/
	rm -rf *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

lint:
	flake8 src/ tests/ examples/