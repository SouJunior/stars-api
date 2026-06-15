# Environment configuration (defaults to local). Set ENV=prod to use the .docker/ configuration.
ENV ?= local

ifeq ($(ENV), local)
  DOCKER_COMPOSE_FILE = docker-compose.local.yml
  API_SERVICE = stars-api-local
else
  DOCKER_COMPOSE_FILE = .docker/docker-compose.yml
  API_SERVICE = stars-api
endif

DOCKER_COMPOSE = docker compose -f $(DOCKER_COMPOSE_FILE)


.PHONY: help start start-d down stop build restart logs shell migrate rollback migration test lint format clean

help: ## Show this help message
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

start: ## Start the application containers in the foreground
	$(DOCKER_COMPOSE) up

start-d: ## Start the application containers in the background (detached)
	$(DOCKER_COMPOSE) up -d

down: ## Stop the application containers
	$(DOCKER_COMPOSE) down

stop: ## Stop the application containers and remove all volumes (database data will be lost)
	$(DOCKER_COMPOSE) down -v

build: ## Rebuild and start the application containers
	$(DOCKER_COMPOSE) up --build

restart: ## Restart the API service container
	$(DOCKER_COMPOSE) restart $(API_SERVICE)

logs: ## View real-time logs of the application containers
	$(DOCKER_COMPOSE) logs -f

shell: ## Open an interactive bash shell in the API service container
	$(DOCKER_COMPOSE) exec $(API_SERVICE) bash

migrate: ## Run all pending database migrations (Alembic)
	$(DOCKER_COMPOSE) exec $(API_SERVICE) alembic upgrade head

rollback: ## Rollback the last database migration
	$(DOCKER_COMPOSE) exec $(API_SERVICE) alembic downgrade -1

migration: ## Create a new database migration. Usage: make migration MSG="migration description"
	@if [ -z "$(MSG)" ]; then \
		echo "Error: MSG is not set. Use: make migration MSG=\"your message\""; \
		exit 1; \
	fi
	$(DOCKER_COMPOSE) exec $(API_SERVICE) alembic revision --autogenerate -m "$(MSG)"

test: ## Run tests using pytest
	@if [ -f venv/bin/pytest ]; then \
		venv/bin/pytest --cov=app; \
	elif [ -f env/bin/pytest ]; then \
		env/bin/pytest --cov=app; \
	else \
		pytest --cov=app; \
	fi

lint: ## Run code linter check (flake8)
	@if [ -f venv/bin/flake8 ]; then \
		venv/bin/flake8 app/ tests/; \
	elif [ -f env/bin/flake8 ]; then \
		env/bin/flake8 app/ tests/; \
	else \
		flake8 app/ tests/; \
	fi

format: ## Format code style (black)
	@if [ -f venv/bin/black ]; then \
		venv/bin/black app/ tests/; \
	elif [ -f env/bin/black ]; then \
		env/bin/black app/ tests/; \
	else \
		black app/ tests/; \
	fi

clean: ## Remove temporary python files and cache
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".coverage" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +
