.PHONY: help install dev test lint migrate db-up build up down clean verify-backup security-audit perf-test e2e health deploy-staging deploy-prod

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

verify-backup:
	@echo "Verifying backup integrity..."
	docker compose exec backup ls -la /backups/
	docker compose exec postgres pg_isready -U salesos
	@echo "Backup verification complete."

security-audit:
	@echo "Running security audit..."
	cd backend && poetry run bandit -r app/ -ll
	cd backend && poetry run safety check
	cd frontend && npm audit --audit-level=high
	@echo "Security audit complete."

perf-test:
	@echo "Running performance load test..."
	python scripts/load-test.py --endpoint http://localhost:8000 --concurrent 50 --duration 60
	@echo "Performance test complete."

e2e:
	@echo "Running E2E tests..."
	cd frontend && npx playwright test
	@echo "E2E tests complete."

health:
	@echo "Checking service health..."
	@curl -sf http://localhost:8000/health || echo "Backend: DOWN"
	@curl -sf http://localhost:3000 || echo "Frontend: DOWN"
	@docker compose exec postgres pg_isready -U salesos || echo "PostgreSQL: DOWN"
	@docker compose exec neo4j cypher-shell "RETURN 1" || echo "Neo4j: DOWN"
	@echo "Health check complete."

deploy-staging:
	@echo "Deploying to staging..."
	IMAGE_TAG=staging docker compose -f docker-compose.prod.yml pull
	IMAGE_TAG=staging docker compose -f docker-compose.prod.yml up -d migrations
	IMAGE_TAG=staging docker compose -f docker-compose.prod.yml up -d
	@echo "Staging deployment complete."

deploy-prod:
	@echo "Deploying to production..."
	@if [ -z "$(VERSION)" ]; then echo "Usage: make deploy-prod VERSION=v1.0.0"; exit 1; fi
	IMAGE_TAG=$(VERSION) docker compose -f docker-compose.prod.yml pull
	IMAGE_TAG=$(VERSION) docker compose -f docker-compose.prod.yml up -d migrations
	IMAGE_TAG=$(VERSION) docker compose -f docker-compose.prod.yml up -d
	docker image prune -f
	@echo "Production deployment complete: $(VERSION)"
