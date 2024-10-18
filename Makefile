# Settings related with https://github.com/Greengage-project/interlink-project
SHELL := /bin/bash

.PHONY: help
help: ## Show this help
	@egrep -h '\s##\s' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

.PHONY: down
down: ## Stops all containers and removes volumes
	docker-compose -f docker-compose.devintegrated.yml down --remove-orphans

#######################
## BUILD IMAGES
#######################

.PHONY: build
build: ## Builds development containers
	docker-compose -f docker-compose.devintegrated.yml build

#######################
## RUN CONTAINERS
#######################

.PHONY: integrated
integrated: down ## Starts integrated development containers
	docker network create traefik-public || true
	docker-compose -f docker-compose.devintegrated.yml up -d