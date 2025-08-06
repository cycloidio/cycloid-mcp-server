# Cycloid MCP Server Makefile
SHELL := /bin/bash

.PHONY: help setup build test clean install dev-server prod-server validate-env simulate-ci

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Development Environment Setup
setup: ## Set up development environment with uv
	@echo "🚀 Setting up development environment..."
	uv venv
	uv sync --dev
	@echo "✅ Development environment ready!"

install: ## Install dependencies
	@echo "📦 Installing dependencies..."
	uv sync --dev

# Development Server (Python Virtual Environment)
dev-server: ## Run the development server using Python virtual environment
	@echo "🐍 Starting development server..."
	@if [ ! -d ".venv" ]; then \
		echo "❌ Virtual environment not found. Run 'make setup' first."; \
		exit 1; \
	fi
	uv run python server.py

# Production Server (Docker)
prod-server: ## Run the production server using Docker
	@echo "🐳 Starting production server..."
	docker build -t cycloid-mcp-server:latest .
	docker run --rm -i cycloid-mcp-server:latest

# Docker commands
build: ## Build the production Docker image
	docker build -t cycloid-mcp-server:latest .

# Testing and Quality (Development Environment)
test: ## Run all tests
	@echo "🧪 Running all tests..."
	uv run pytest tests/ -v

type-check: ## Run pyright type checking
	@echo "🔍 Running pyright type checking..."
	uv run pyright src/

lint: ## Run PEP 8 linting with flake8
	@echo "🎨 Running PEP 8 linting..."
	uv run flake8 src/ tests/

format: ## Format code with black and isort
	@echo "✨ Formatting code..."
	uv run black src/ tests/
	uv run isort src/ tests/

quality-check: ## Run all quality checks (tests + type checking + linting)
	@echo "✅ Running all quality checks..."
	@make test
	@make type-check
	@make lint

validate-env: ## Validate local environment matches CI
	@echo "🔍 Validating environment..."
	@python_version=$$(python --version 2>&1 | cut -d' ' -f2); \
	if [[ ! "$$python_version" =~ ^3\.13\. ]]; then \
		echo "❌ Python version mismatch! Expected: 3.13.x, Found: $$python_version"; \
		echo "   Install Python 3.13.x to match CI environment"; \
		exit 1; \
	fi; \
	echo "✅ Python version: $$python_version"
	@if ! command -v uv &> /dev/null; then \
		echo "❌ uv not found! Install with: curl -LsSf https://astral.sh/uv/install.sh | sh"; \
		exit 1; \
	fi
	@uv_version=$$(uv --version | cut -d' ' -f2); \
	echo "✅ uv version: $$uv_version"
	@if [[ ! -f "pyrightconfig.json" ]]; then \
		echo "❌ pyrightconfig.json not found!"; \
		exit 1; \
	fi
	@pyright_python=$$(grep '"pythonVersion"' pyrightconfig.json | head -1 | cut -d'"' -f4); \
	if [[ "$$pyright_python" != "3.13" ]]; then \
		echo "❌ pyrightconfig.json Python version mismatch! Expected: 3.13, Found: $$pyright_python"; \
		exit 1; \
	fi; \
	echo "✅ pyrightconfig.json Python version: $$pyright_python"
	@echo "✅ Environment validation complete!"

simulate-ci: validate-env ## Validate local environment and run quality checks
	@echo "🔍 Validating local development environment..."
	./scripts/simulate-ci.sh

test-ci: ## Test CI workflow locally
	@echo "🧪 Testing CI workflow locally..."
	./scripts/test-ci.sh

# Health and Status
health-check: ## Check if the server is healthy
	@echo "🏥 Checking server health..."
	docker ps | grep cycloid-mcp-server || echo "❌ Container not running"

clean: ## Clean up development artifacts
	@echo "🧹 Cleaning up..."
	rm -rf .pytest_cache/
	rm -rf __pycache__/
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "✅ Cleanup complete!"

clean-docker: ## Clean up Docker artifacts
	@echo "🧹 Cleaning up Docker artifacts..."
	docker system prune -f
	docker image rm cycloid-mcp-server:latest 2>/dev/null || true
	@echo "✅ Docker cleanup complete!"
