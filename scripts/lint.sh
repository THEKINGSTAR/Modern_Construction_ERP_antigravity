#!/usr/bin/env bash
set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_ROOT}"

echo "=========================================================="
echo " Running Modern Construction ERP Code Quality Checks"
echo "=========================================================="

# Select appropriate python binary
if [ -x "/usr/bin/python3" ]; then
    PYTHON_BIN="/usr/bin/python3"
else
    PYTHON_BIN="$(command -v python3)"
fi

echo "[1/2] Checking Python Backend Syntax & Compilation..."
"${PYTHON_BIN}" -m compileall apps/api -q
echo "      Python syntax check passed."

echo "[2/2] Running Frontend ESLint (Next.js)..."
cd "${REPO_ROOT}/apps/web"
npm run lint
echo "      Frontend lint passed."

echo "=========================================================="
echo " All linting & code quality checks passed successfully!"
echo "=========================================================="
