#!/usr/bin/env bash
set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_ROOT}"

echo "=========================================================="
echo " Starting Modern Construction ERP (Development Environment)"
echo "=========================================================="

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is required but not installed." >&2
    exit 1
fi

echo "[1/4] Starting Docker services (PostgreSQL, Redis, API, Web)..."
docker compose up -d

echo "[2/4] Awaiting PostgreSQL readiness (localhost:5434)..."
MAX_ATTEMPTS=30
ATTEMPT=0
while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    if docker compose exec -T db pg_isready -U postgres -d erp >/dev/null 2>&1; then
        echo "      PostgreSQL is healthy and accepting connections."
        break
    fi
    ATTEMPT=$((ATTEMPT + 1))
    sleep 1
done

if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
    echo "Warning: Database health check timed out. Proceeding..." >&2
fi

echo "[3/4] Awaiting FastAPI backend health (http://localhost:8000/api/v1/health)..."
ATTEMPT=0
while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    if curl -s -f http://localhost:8000/api/v1/health >/dev/null 2>&1; then
        echo "      FastAPI backend is online."
        break
    fi
    ATTEMPT=$((ATTEMPT + 1))
    sleep 1
done

if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
    echo "Warning: API health check timed out. Proceeding..." >&2
fi

echo "[4/4] Verifying Next.js frontend accessibility (http://localhost:3000)..."
if curl -s http://localhost:3000 >/dev/null 2>&1; then
    echo "      Next.js web portal is responding."
else
    echo "      Next.js is compiling/starting up."
fi

echo "=========================================================="
echo " Modern Construction ERP is ready!"
echo "----------------------------------------------------------"
echo " Web Portal:   http://localhost:3000"
echo " API Endpoint: http://localhost:8000/api/v1"
echo " API Docs:     http://localhost:8000/docs"
echo " Database:     localhost:5434 (db: erp, user: postgres)"
echo " Redis:        localhost:6379"
echo "=========================================================="
