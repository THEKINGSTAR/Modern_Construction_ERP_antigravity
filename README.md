# Modern Construction ERP

A comprehensive, multi-tenant Enterprise Resource Planning (ERP) system designed specifically for the construction industry. Built with a modern Python/FastAPI backend and robust PostgreSQL database schema, this system provides full-lifecycle project management, accounting, procurement, inventory, and commercial management capabilities.

## 🏗️ Architecture

The system is built on a scalable, modern technology stack:
- **Backend:** FastAPI (Python 3.11+)
- **Database:** PostgreSQL (with SQLAlchemy 2.0 ORM & Alembic for migrations)
- **Validation:** Pydantic V2
- **Testing:** Pytest (with AnyIO for async testing)
- **Deployment:** Docker & Docker Compose
- **CI/CD:** GitHub Actions

### Key Architectural Principles
- **Multi-Tenancy:** Strict tenant isolation at the database row level (using `TenantAwareMixin`).
- **Idempotency & Atomicity:** Financial and inventory transactions use atomic operations with database-level constraints.
- **Golden Rules:**
  - **Accounting:** Double-entry accounting system where every journal entry strictly balances (Sum of Debits == Sum of Credits).
  - **Inventory:** Immutable ledger-based inventory with strict prevention of negative stock.
- **Traceability:** Every actual cost and management report is traceable to source transactions.

## 🗂️ Project Structure

```
Modern_Construction_ERP/
├── apps/
│   ├── api/
│   │   ├── app/
│   │   │   ├── core/           # Security, context, mixins, config
│   │   │   ├── models/         # SQLAlchemy ORM Models (domain-driven)
│   │   │   ├── schemas/        # Pydantic Schemas for Request/Response
│   │   │   ├── services/       # Business Logic & Orchestration
│   │   │   └── api/            # FastAPI Routers
│   │   └── tests/              # Pytest Suite (Unit, Integration, E2E)
├── infrastructure/
│   └── scripts/                # Database Backup/Restore & Maintenance
├── .github/
│   └── workflows/              # CI/CD pipelines (ci.yml)
├── docker-compose.prod.yml     # Production deployment configuration
├── docker-compose.staging.yml  # Staging deployment configuration
├── BUILD_STATUS.md             # Project build phases and status
└── CHECKPOINTS.md              # Checkpoints for verified recovery points
```

## 🧩 Core Modules (Domains)

The ERP covers the complete lifecycle of a construction company:

1. **Identity & Foundation:** Multi-tenancy, authentication, authorization, localization, departments, and legal entities.
2. **Project Management:** Project setup, Work Breakdown Structure (WBS), cost codes, and budget estimates.
3. **Commercial Management:** Contracts, Subcontracts, Client Payment Applications, Subcontractor Payments, and Change Orders.
4. **Procurement:** Requisitions, Purchase Orders, and Subcontracts.
5. **Inventory & Materials:** Warehouses, Material Issues, Goods Receipts, Transfers, and Adjustments (Weighted Average Cost valuation).
6. **Financials & Accounting:** Chart of Accounts, General Ledger, Journals, Accounts Payable (AP), Accounts Receivable (AR), and Bank Reconciliation.
7. **Equipment Management:** Asset tracking, usage logs, fuel consumption, and maintenance records.
8. **Workforce Management:** Employees, Timesheets, Project Assignments, and Leave Requests.
9. **Enterprise Services:** Documents, Approvals, Notifications, and Events.
10. **Management Reporting:** Real-time dashboards, project profitability, budget vs actual, AP/AR aging, and trial balance.

## 🚀 Getting Started

### Prerequisites
- Docker and Docker Compose
- Python 3.11+
- PostgreSQL (if running locally without Docker)

### Local Development Setup
1. **Clone the repository.**
2. **Set up the virtual environment:**
   ```bash
   cd apps/api
   python -m venv venv
   source venv/bin/activate  # Or `venv\Scripts\activate` on Windows
   pip install -r requirements.txt
   ```
3. **Run database migrations:**
   *(Ensure you have a PostgreSQL instance running locally)*
   ```bash
   alembic upgrade head
   ```
4. **Run the development server:**
   ```bash
   uvicorn app.main:app --reload
   ```

### Running Tests
The project features comprehensive tests, including E2E Golden tests for Production Readiness.
```bash
cd apps/api
pytest tests/ -v
```
*(To run only the Golden Rules E2E test: `pytest tests/test_e2e_production.py -v`)*

## 🔒 Production Readiness
The application is fully configured for production deployment (Stage 18 Completed).
- Use `docker-compose.prod.yml` to spin up production services.
- Database backup and restore scripts are located in `infrastructure/scripts/`.
- CI/CD workflows enforce tests, type checking, and security scans on every PR.

## 📋 License
Proprietary / Internal - Do Not Distribute
