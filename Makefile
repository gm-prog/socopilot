.PHONY: help up down build logs migrate verify shell-api shell-worker

COMPOSE_FILE := docker/docker-compose.yml
COMPOSE := docker compose -f $(COMPOSE_FILE)

help:
	@echo "SOCoPilot — Phase 0 commands"
	@echo "  make up       - Start all services"
	@echo "  make down     - Stop all services"
	@echo "  make build    - Build Docker images"
	@echo "  make logs     - Tail compose logs"
	@echo "  make migrate  - Run Alembic migrations"
	@echo "  make verify   - Run verification checks"
	@echo "  make shell-api - Shell into API container"

up: build
	$(COMPOSE) up -d
	@echo "SOCoPilot is starting. API: http://localhost:8000  Frontend: http://localhost:3000"

down:
	$(COMPOSE) down

build:
	$(COMPOSE) build

logs:
	$(COMPOSE) logs -f

migrate:
	$(COMPOSE) run --rm api alembic upgrade head

verify:
	powershell -ExecutionPolicy Bypass -File scripts/verify.ps1

shell-api:
	$(COMPOSE) exec api /bin/sh

shell-worker:
	$(COMPOSE) exec worker /bin/sh
