# Gambling Comment Detector - Makefile
# Common development commands for the project

.PHONY: help dev dev-backend dev-frontend test test-backend test-frontend lint lint-backend lint-frontend migrate migrate-new docker-up docker-down docker-build docker-logs clean install install-backend install-frontend

# Default target
help:
	@echo "Gambling Comment Detector - Development Commands"
	@echo ""
	@echo "Development:"
	@echo "  make dev              - Start all development servers"
	@echo "  make dev-backend      - Start backend development server"
	@echo "  make dev-frontend     - Start frontend development server"
	@echo ""
	@echo "Testing:"
	@echo "  make test             - Run all tests"
	@echo "  make test-backend     - Run backend tests"
	@echo "  make test-properties  - Run property-based tests only"
	@echo "  make test-cov         - Run tests with coverage report"
	@echo ""
	@echo "Linting:"
	@echo "  make lint             - Run all linters"
	@echo "  make lint-backend     - Run backend linters"
	@echo "  make lint-frontend    - Run frontend linters"
	@echo ""
	@echo "Database:"
	@echo "  make migrate          - Run database migrations"
	@echo "  make migrate-new      - Create new migration (MSG=description)"
	@echo "  make migrate-down     - Downgrade last migration"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-up        - Start all Docker services"
	@echo "  make docker-down      - Stop all Docker services"
	@echo "  make docker-build     - Build Docker images"
	@echo "  make docker-logs      - View Docker logs"
	@echo ""
	@echo "Setup:"
	@echo "  make install          - Install all dependencies"
	@echo "  make install-backend  - Install backend dependencies"
	@echo "  make install-frontend - Install frontend dependencies"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean            - Remove generated files and caches"

# ============================================================================
# Development
# ============================================================================

dev: docker-up
	@echo "Starting development environment..."
	@echo "Backend API: http://localhost:8000"
	@echo "Frontend: http://localhost:3000"
	@echo "Flower Dashboard: http://localhost:5555"

dev-backend:
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend:
	cd frontend && npm run dev

# ============================================================================
# Testing
# ============================================================================

test: test-backend

test-backend:
	cd backend && python -m pytest tests/ -v

test-properties:
	cd backend && python -m pytest tests/properties/ -v

test-cov:
	cd backend && python -m pytest tests/ -v --cov=app --cov-report=html --cov-report=term-missing

# ============================================================================
# Linting
# ============================================================================

lint: lint-backend lint-frontend

lint-backend:
	cd backend && python -m ruff check app/ tests/ || true
	cd backend && python -m ruff format --check app/ tests/ || true

lint-frontend:
	cd frontend && npm run lint || true

# ============================================================================
# Database Migrations
# ============================================================================

migrate:
	cd backend && alembic upgrade head

migrate-new:
	@if [ -z "$(MSG)" ]; then \
		echo "Error: Please provide a migration message with MSG=description"; \
		exit 1; \
	fi
	cd backend && alembic revision --autogenerate -m "$(MSG)"

migrate-down:
	cd backend && alembic downgrade -1

migrate-history:
	cd backend && alembic history

# ============================================================================
# Docker
# ============================================================================

docker-up:
	docker compose up -d

docker-down:
	docker compose down

docker-build:
	docker compose build

docker-logs:
	docker compose logs -f

docker-restart:
	docker compose restart

docker-clean:
	docker compose down -v --remove-orphans

# ============================================================================
# Installation
# ============================================================================

install: install-backend install-frontend

install-backend:
	cd backend && pip install -r requirements.txt

install-frontend:
	cd frontend && npm install

# ============================================================================
# Cleanup
# ============================================================================

clean:
	@echo "Cleaning up generated files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".hypothesis" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	rm -rf backend/htmlcov 2>/dev/null || true
	rm -rf frontend/.next 2>/dev/null || true
	rm -rf frontend/node_modules/.cache 2>/dev/null || true
	@echo "Cleanup complete."
