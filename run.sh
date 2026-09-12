#!/bin/bash
# run.sh - Runs Modern Construction ERP in production mode

set -e

echo "Checking requirements..."

command_exists() {
  command -v "$1" >/dev/null 2>&1
}

# Check for Docker
if ! command_exists docker; then
    echo "Error: Docker is not installed. Please run 'sudo ./install.sh' first."
    exit 1
fi

# Check for Docker Compose
DOCKER_COMPOSE_CMD=""
if docker compose version >/dev/null 2>&1; then
    DOCKER_COMPOSE_CMD="docker compose"
elif command_exists docker-compose; then
    DOCKER_COMPOSE_CMD="docker-compose"
else
    echo "Error: Docker Compose is not installed. Please run 'sudo ./install.sh' first."
    exit 1
fi

# Check for .env file
if [ ! -f .env ]; then
    echo "Error: .env file not found. Please run 'sudo ./install.sh' or create it manually from .env.example."
    exit 1
fi

echo "Starting Modern Construction ERP services in production mode..."

# Build and start services
$DOCKER_COMPOSE_CMD -f docker-compose.prod.yml build
$DOCKER_COMPOSE_CMD -f docker-compose.prod.yml up -d

echo "Services started. Checking status..."
$DOCKER_COMPOSE_CMD -f docker-compose.prod.yml ps

echo "Modern Construction ERP is now running!"
echo "To view logs, run: $DOCKER_COMPOSE_CMD -f docker-compose.prod.yml logs -f"
echo "To stop services, run: $DOCKER_COMPOSE_CMD -f docker-compose.prod.yml down"
