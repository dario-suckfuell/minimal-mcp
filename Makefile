# Makefile for MCP Private Database

.PHONY: setup install run test fmt lint clean help

# Default target
help:
	@echo "Available targets:"
	@echo "  setup    - Set up local environment file"
	@echo "  install  - Install dependencies"
	@echo "  run      - Run the MCP server"
	@echo "  test     - Run tests"
	@echo "  fmt      - Format code with black"
	@echo "  lint     - Lint code with ruff"
	@echo "  clean    - Clean up temporary files"

# Set up local environment
setup:
	python3 setup_local.py

# Install dependencies
install:
	pip install -r requirements.txt

# Run the MCP server
run:
	python -m mcp_private_db.main

# Run tests
test:
	pytest tests/ -v

# Format code
fmt:
	black mcp_private_db/ tests/

# Lint code
lint:
	ruff check mcp_private_db/ tests/

# Clean up
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
