.PHONY: help install dev test lint migrate db-up build up down clean verify-backup security-audit perf-test e2e health deploy-staging deploy-prod deploy-prod-k8s deploy-prod-full rollback backup smoke-test smoke-test-staging

help:
	@echo "SalesOS Reference Implementation"
	@echo ""
	@echo "Usage:"
	@echo "  make install              Install all dependencies"
	@echo "  make dev                  Start development environment (docker-compose)"
	@echo "  make test                 Run all tests"
	@echo "  make lint                 Run linters"
	@echo "  make migrate              Run database migrations"
	@echo "  make db-up                Upgrade database to latest migration"
	@echo "  make build                Build all Docker images"
	@echo "  make up                   Start all services (detached)"
	@echo "  make down                 Stop all services"
	@echo "  make clean                Remove all volumes and caches"
	@echo "  make reset                Full reset: down -> clean -> build -> up"
	@echo "  make logs                 Tail logs from all services"
	@echo "  make health               Check service health"
	@echo "  make smoke-test           Run comprehensive smoke tests"
	@echo "  make deploy-prod V=vX.Y   Docker Compose production deploy"
	@echo "  make deploy-prod-k8s V=vX.Y  K8s production deploy"
	@echo "  make deploy-prod-full V=vX.Y Full production deploy + tests"
	@echo "  make rollback             Rollback to previous K8s version"
	@echo "  make backup               Run database backup"
	@echo "  make security-audit       Run security audit"
	@echo "  make perf-test            Run performance load test"
	@echo "  make e2e                  Run E2E tests"

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

smoke-test:
	@echo "Running comprehensive smoke tests..."
	@powershell -File ./scripts/smoke-test.ps1 -BaseUrl http://localhost:8000 -FrontendUrl http://localhost:3000
	@echo "Smoke tests complete."

smoke-test-staging:
	@echo "Running smoke tests against staging..."
	@powershell -File ./scripts/smoke-test.ps1 -BaseUrl $(STAGING_API_URL) -FrontendUrl $(STAGING_FRONTEND_URL)
	@echo "Staging smoke tests complete."

deploy-staging:
	@echo "Deploying to staging..."
	IMAGE_TAG=staging docker compose -f docker-compose.prod.yml pull
	IMAGE_TAG=staging docker compose -f docker-compose.prod.yml up -d migrations
	IMAGE_TAG=staging docker compose -f docker-compose.prod.yml up -d
	@echo "Staging deployment complete."

deploy-prod:
	@echo "========================================"
	@echo "  SalesOS Production Deployment"
	@echo "========================================"
	@if [ -z "$(VERSION)" ]; then echo "Usage: make deploy-prod VERSION=v5.1.0"; exit 1; fi
	@echo "Version: $(VERSION)"
	@echo ""
	@echo "[1/5] Tagging images..."
	IMAGE_TAG=$(VERSION) docker compose -f docker-compose.prod.yml pull
	@echo "[2/5] Running migrations..."
	IMAGE_TAG=$(VERSION) docker compose -f docker-compose.prod.yml up -d migrations
	@echo "[3/5] Starting services..."
	IMAGE_TAG=$(VERSION) docker compose -f docker-compose.prod.yml up -d
	@echo "[4/5] Waiting for health..."
	@sleep 15
	@echo "[5/5] Running smoke tests..."
	@powershell -File ./scripts/smoke-test.ps1 -BaseUrl http://localhost:8000 -FrontendUrl http://localhost:3000 -MaxRetries 15
	docker image prune -f
	@echo "✅ Production deployment complete: $(VERSION)"

deploy-prod-k8s:
	@echo "========================================"
	@echo "  SalesOS K8s Production Deployment"
	@echo "========================================"
	@if [ -z "$(VERSION)" ]; then echo "Usage: make deploy-prod-k8s VERSION=v5.1.0"; exit 1; fi
	@echo "Version: $(VERSION)"
	@echo ""
	@echo "[1/4] Updating images..."
	kubectl set image deployment/backend backend=ghcr.io/ragheeda-boop/salesos/backend:$(VERSION) -n salesos
	kubectl set image deployment/frontend frontend=ghcr.io/ragheeda-boop/salesos/frontend:$(VERSION) -n salesos
	@echo "[2/4] Waiting for rollout..."
	kubectl rollout status deployment/backend -n salesos --timeout=300s
	kubectl rollout status deployment/frontend -n salesos --timeout=300s
	@echo "[3/4] Running smoke tests..."
	@powershell -File ./scripts/smoke-test.ps1 -BaseUrl https://api.salesos.com -FrontendUrl https://app.salesos.com
	@echo "[4/4] Cleaning up old images..."
	kubectl delete pod -n salesos -l image-pull-policy=Always 2>/dev/null || true
	@echo "========================================"
	@echo "  K8s production deployment complete: $(VERSION)"
	@echo "========================================"

deploy-prod-full: smoke-test security-audit deploy-prod
	@echo "✅ Full production deployment complete"

rollback:
	@echo "Rolling back to previous version..."
	kubectl rollout undo deployment/backend -n salesos
	kubectl rollout undo deployment/frontend -n salesos
	kubectl rollout status deployment/backend -n salesos --timeout=300s
	kubectl rollout status deployment/frontend -n salesos --timeout=300s
	@powershell -File ./scripts/smoke-test.ps1 -BaseUrl https://api.salesos.com -FrontendUrl https://app.salesos.com
	@echo "✅ Rollback complete"

backup:
	@echo "Running backup..."
	@powershell -File ./scripts/backup.ps1 -Upload
	@echo "✅ Backup complete"
