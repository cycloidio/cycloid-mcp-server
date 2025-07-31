.PHONY: install test lint format type-check clean debug validate test-server setup-env docker-build docker-dev docker-prod docker-clean

# Development commands (for local development without Docker)
install:
	uv sync

test:
	uv run pytest

lint:
	uv run black --check src
	uv run isort --check-only src
	uv run flake8 src
	uv run mypy src

format:
	uv run black src
	uv run isort src

type-check:
	uv run mypy src

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

debug:
	uv run python scripts/debug_server.py

validate:
	uv run python scripts/validate_setup.py

test-server:
	uv run python scripts/test_server.py

setup-env:
	uv run python scripts/update_env.py

# Docker commands (recommended)
docker-build:
	docker build -f Dockerfile.dev -t cycloid-mcp-server:dev .

docker-prod:
	docker build -f Dockerfile -t cycloid-mcp-server:latest .

docker-dev:
	docker-compose -f docker-compose.dev.yml up --build

docker-prod-run:
	docker-compose up --build

docker-clean:
	docker system prune -f
	docker image prune -f
	docker volume prune -f

# Quick development with Docker
dev: docker-build
	docker run --rm -it \
		-v $(PWD):/app \
		--env-file .env \
		cycloid-mcp-server:dev

# Production run
prod: docker-prod
	docker run --rm -it \
		--env-file .env \
		cycloid-mcp-server:latest

# Quick setup for development
setup: setup-env docker-build
	@echo "✅ Development environment setup complete!"
	@echo "📝 To use with Cursor, create ~/.cursor/mcp.json with:"
	@echo "   {"
	@echo "     \"mcpServers\": {"
	@echo "       \"cycloid\": {"
	@echo "         \"command\": \"docker\","
	@echo "         \"args\": ["
	@echo "           \"run\","
	@echo "           \"--rm\","
	@echo "           \"-i\","
	@echo "           \"--env-file\", \"$(PWD)/.env\","
	@echo "           \"cycloid-mcp-server:dev\""
	@echo "         ]"
	@echo "       }"
	@echo "     }"
	@echo "   }"

# Run server locally (for testing)
run-local:
	python3 server.py 