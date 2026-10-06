#!/usr/bin/env bash
set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_ROOT}"

echo "=========================================================="
echo " Seeding Modern Construction ERP Demo & Reference Data"
echo "=========================================================="

# Select appropriate python binary
if [ -x "/usr/bin/python3" ]; then
    PYTHON_BIN="/usr/bin/python3"
else
    PYTHON_BIN="$(command -v python3)"
fi

export DATABASE_URL="${DATABASE_URL:-postgresql://postgres:postgres@localhost:5434/erp}"
export REDIS_URL="${REDIS_URL:-redis://localhost:6379/0}"
export SECRET_KEY="${SECRET_KEY:-demo_secret_key_for_development_and_seeding_only}"
export ENVIRONMENT="${ENVIRONMENT:-development}"

echo "Running seed script with target: ${DATABASE_URL}"
"${PYTHON_BIN}" scripts/seed.py

echo "=========================================================="
echo " Demo & reference data seeding completed successfully."
echo "=========================================================="
