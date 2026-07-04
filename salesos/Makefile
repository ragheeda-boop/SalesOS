.PHONY: help install dev test lint migrate db-up build up down clean

help:
	@echo "SalesOS Reference Implementation"
	@echo ""
	@echo "Usage:"
	@echo "  make install     Install all dependencies"
	@echo "  make dev         Start development environment (docker-compose)"
	@echo "  make test        Run all tests"
	@echo "  make lint        Run linters"
	@echo "  make migrate     Run database migrations"
	@echo "  make db-up       Upgrade database to latest migration"
	@echo "  make build       Build all Docker images"
	@echo "  make up          Start all services (detached)"
	@echo "  make down        Stop all services"
	@echo "  make clean       Remove all volumes and caches"
	@echo "  make reset       Full reset: down -> clean -> build -> up"
	@echo "  make logs        Tail logs from all services"

install:
	cd backend && poetry install
	cd frontend && npm install

dev:
	docker compose up --build

test:
	cd backend && poetry run pytest -v --cov=app --cov-report=term-missing
	cd frontend && npm run test

lint:
	cd backend && poetry run ruff check app/ tests/
	cd backend && poetry run mypy app/
	cd frontend && npm run lint

migrate:
	cd backend && poetry run alembic upgrade head

db-up:
	cd backend && poetry run alembic upgrade head

db-down:
	cd backend && poetry run alembic downgrade -1

db-new:
	cd backend && poetry run alembic revision --autogenerate -m "$(message)"

build:
	docker compose build

up:
	docker compose up -d --build

down:
	docker compose down

clean:
	docker compose down -v
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .next -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true

reset: down clean build up

logs:
	docker compose logs -f
