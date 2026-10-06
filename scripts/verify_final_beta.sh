#!/usr/bin/env bash
set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_ROOT}"

echo "======================================================================"
echo " MODERN CONSTRUCTION ERP — UNIFIED FINAL BETA VERIFICATION PIPELINE"
echo "======================================================================"
START_TIME=$(date +%s)

# Select Python
if [ -x "/usr/bin/python3" ]; then
    PYTHON_BIN="/usr/bin/python3"
else
    PYTHON_BIN="$(command -v python3)"
fi

echo ""
echo ">>> STEP 1/7: Running Static Code Quality & Lint Checks..."
./scripts/lint.sh

echo ""
echo ">>> STEP 2/7: Running Full Backend Test Harness (pytest)..."
cd "${REPO_ROOT}/apps/api"
"${PYTHON_BIN}" -m pytest tests/ -v
cd "${REPO_ROOT}"

echo ""
echo ">>> STEP 3/7: Building Production Frontend Bundle (Next.js)..."
cd "${REPO_ROOT}/apps/web"
npm run build
cd "${REPO_ROOT}"

echo ""
echo ">>> STEP 4/7: Testing Deterministic Demo Data Seeding & Idempotency..."
./scripts/seed.sh

echo ""
echo ">>> STEP 5/7: Executing Baseline 70-Check E2E Integration Suite..."
"${PYTHON_BIN}" scripts/test_demo_e2e.py

echo ""
echo ">>> STEP 6/7: Executing Workflow 3 (Commercial Billing & AR Cash Settlement)..."
"${PYTHON_BIN}" scripts/verify_workflow_3_ar.py

echo ""
echo ">>> STEP 7/7: Executing Stage 34 Authoritative 18-Step Business Journey Suite..."
"${PYTHON_BIN}" scripts/test_user_journey_e2e.py

END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))

echo ""
echo "======================================================================"
echo "🎉 FINAL BETA VERIFICATION CAMPAIGN COMPLETE — ALL 22 GATES SATISFIED"
echo "   Total Pipeline Duration: ${ELAPSED} seconds"
echo "======================================================================"
