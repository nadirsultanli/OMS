# Disable BuildKit to avoid build issues
export COMPOSE_DOCKER_CLI_BUILD=0
export DOCKER_BUILDKIT=0

APP_CONTAINER = backend_oms-backend_1
EXEC = docker exec -it
DC = docker-compose
DC_FILE = docker-compose.yaml

# Declare phony targets (commands, not files)
.PHONY: up down logs build stop clean exec logs-docker install install-prod update test venv activate clean-venv

# Start services in detached mode
up:
	${DC} -f ${DC_FILE} up -d

# Stop and remove services
down:
	${DC} -f ${DC_FILE} down

# View logs from services
logs:
	${DC} -f ${DC_FILE} logs -f

# Rebuild and start services
build:
	${DC} -f ${DC_FILE} up --build

# Stop services without removing containers
stop:
	${DC} -f ${DC_FILE} stop

# Remove containers, networks, and volumes
clean:
	${DC} -f ${DC_FILE} down --volumes

# Go inside backend container
exec:
	${EXEC} ${APP_CONTAINER} bash

# Logs of backend container
logs-docker:
	docker logs ${APP_CONTAINER}

# Create virtual environment
venv:
	python3 -m venv venv

# Activate virtual environment (run this in your shell)
activate:
	@echo "Run: source venv/bin/activate"

# Install dependencies in virtual environment
install:
	pip install -r requirements-dev.txt

# Install dependencies for production
install-prod:
	pip install -r requirements.txt

# Update dependencies
update:
	pip install --upgrade -r requirements-dev.txt

# General for testing(All) not from container
test:
	pytest

# Clean virtual environment
clean-venv:
	rm -rf venv