#!/usr/bin/env bash
set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "========================================="
echo "Running Modern Construction ERP Tests"
echo "========================================="

echo "[1/2] Running Backend Tests (pytest)..."
cd "${REPO_ROOT}/apps/api"
python3 -m pytest tests/ -v

echo "========================================="
echo "[2/2] Building Frontend (Next.js)..."
cd "${REPO_ROOT}/apps/web"
npm run build

echo "========================================="
echo "All backend and frontend test/build suites completed successfully."
