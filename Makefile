# Cycloid MCP Server Makefile

.PHONY: help setup build test clean install dev-server prod-server

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