SHELL := /bin/bash

# Auto-detect docker compose v2 (`docker compose`) vs v1 (`docker-compose`).
# Override with: make <target> DC="docker-compose"
DC ?= $(shell if docker compose version >/dev/null 2>&1; then echo "docker compose"; \
              elif command -v docker-compose >/dev/null 2>&1; then echo "docker-compose"; \
              else echo ""; fi)

# Compose file selection. Override with: make <target> FILE=docker-compose.yml
FILE ?= docker-compose-dev.yml
COMPOSE := $(DC) -f $(FILE)

.PHONY: help
help: ## Show this help
	@egrep -h '\s##\s' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "Using: $(COMPOSE)"

.PHONY: check
check: ## Verify docker compose is available
	@if [ -z "$(DC)" ]; then \
		echo "ERROR: neither 'docker compose' (v2) nor 'docker-compose' (v1) found in PATH."; \
		exit 1; \
	fi
	@echo "Using compose command: $(DC)"
	@echo "Using compose file:    $(FILE)"

.PHONY: setup
setup: ## First-time setup: install Docker if needed, create .env if needed
	@if [ -z "$(DC)" ]; then \
		echo ""; \
		echo "  Docker Compose not found. Installing automatically..."; \
		echo ""; \
		if command -v apt-get >/dev/null 2>&1; then \
			echo "  [apt] Installing docker.io and docker-compose-v2 ..."; \
			sudo apt-get update -qq && \
			sudo apt-get install -y docker.io docker-compose-v2 && \
			sudo usermod -aG docker $$USER 2>/dev/null || true && \
			( sudo service docker start 2>/dev/null || sudo systemctl start docker 2>/dev/null || true ); \
		elif command -v dnf >/dev/null 2>&1; then \
			echo "  [dnf] Installing docker and docker-compose-plugin ..."; \
			sudo dnf install -y docker docker-compose-plugin && \
			sudo systemctl enable --now docker && \
			sudo usermod -aG docker $$USER 2>/dev/null || true; \
		elif command -v brew >/dev/null 2>&1; then \
			echo "  [brew] Installing Docker via Homebrew ..."; \
			brew install --cask docker && \
			open /Applications/Docker.app && \
			echo "  Waiting for Docker Desktop to start (30 s) ..." && \
			sleep 30; \
		else \
			echo ""; \
			echo "  ERROR: Cannot auto-install Docker on this system."; \
			echo "  Please install it manually: https://docs.docker.com/get-docker/"; \
			echo ""; \
			exit 1; \
		fi; \
		echo ""; \
		echo "  Docker installed. Restarting..."; \
		echo ""; \
		exec $(MAKE) dev; \
	fi
	@if [ ! -f .env ]; then \
		echo ""; \
		echo "================================================"; \
		echo "  First run detected -- no .env file found     "; \
		echo "================================================"; \
		echo ""; \
		printf "  Choose setup mode:\n"; \
		printf "    [A] Automatic  -- use defaults from .env.sample (recommended)\n"; \
		printf "    [C] Customize  -- open .env in your editor before starting\n"; \
		echo ""; \
		printf "  Your choice [A/c]: "; \
		read -r CHOICE; \
		cp .env.sample .env; \
		case "$$CHOICE" in \
			[Cc]*) \
				echo ""; \
				echo "  Opening .env for editing ..."; \
				$${EDITOR:-vi} .env; \
				echo ""; \
				echo "  Configuration saved."; \
				;; \
			*) \
				echo ""; \
				echo "  Auto-configured: .env created from .env.sample."; \
				echo "  You can edit .env at any time to change settings."; \
				;; \
		esac; \
		echo ""; \
	fi

#######################
## BUILD IMAGES
#######################

.PHONY: build
build: check ## Build all containers
	$(COMPOSE) build

.PHONY: pull
pull: check ## Pull latest images for services that use them
	$(COMPOSE) pull

#######################
## RUN CONTAINERS
#######################

.PHONY: up
up: check ## Start all containers in background
	docker network create traefik-public 2>/dev/null || true
	$(COMPOSE) up -d

.PHONY: up-fg
up-fg: check ## Start all containers in foreground (logs attached)
	docker network create traefik-public 2>/dev/null || true
	$(COMPOSE) up

.PHONY: integrated
integrated: down ## Start integrated dev stack (docker-compose.devintegrated.yml)
	docker network create traefik-public 2>/dev/null || true
	$(DC) -f docker-compose.devintegrated.yml up -d

.PHONY: dev
dev: setup down ## Start dev stack (docker-compose-dev.yml)
	docker network create traefik-public 2>/dev/null || true
	$(DC) -f docker-compose-dev.yml up -d

.PHONY: dev-nodb
dev-nodb: down ## Start dev stack without DB (docker-compose-dev-withoutDB.yml)
	docker network create traefik-public 2>/dev/null || true
	$(DC) -f docker-compose-dev-withoutDB.yml up -d

.PHONY: restart
restart: check ## Restart all services
	$(COMPOSE) restart

.PHONY: stop
stop: check ## Stop containers without removing them
	$(COMPOSE) stop

.PHONY: down
down: check ## Stop and remove containers, networks
	$(COMPOSE) down --remove-orphans

.PHONY: clean
clean: check ## Stop and remove containers, networks AND volumes (DESTRUCTIVE)
	$(COMPOSE) down --remove-orphans --volumes

#######################
## INSPECTION
#######################

.PHONY: ps
ps: check ## Show running containers
	$(COMPOSE) ps

.PHONY: logs
logs: check ## Tail logs from all services (Ctrl+C to exit)
	$(COMPOSE) logs -f --tail=100

.PHONY: logs-api
logs-api: check ## Tail logs from the api service
	$(COMPOSE) logs -f --tail=100 api

#######################
## SHELL ACCESS
#######################

.PHONY: shell-api
shell-api: check ## Open a shell inside the api container
	$(COMPOSE) exec api /bin/bash

.PHONY: shell-db
shell-db: check ## Open a psql shell inside the postgres container
	$(COMPOSE) exec postgrespostgres psql -U $${DB_USER:-postgres} -d $${DB_NAME:-postgres}
