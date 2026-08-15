from fastapi import APIRouter
from app.api.endpoints import (
    auth,
    settings,
    projects,
    clients,
    contracts,
    wbs,
    cost_codes,
    boq,
    estimates,
    budgets,
    suppliers,
    requisitions,
    rfqs,
    quotations,
    purchase_orders,
    inventory,
    project_cost,
    accounting,
    ap,
    ar,
    bank,
    commercial,
    hr,
    equipment,
    documents,
    approvals,
    notifications,
    reports
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(settings.router, prefix="/settings", tags=["settings"])
api_router.include_router(clients.router, prefix="/clients", tags=["clients"])
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(contracts.router, prefix="/contracts", tags=["contracts"])
api_router.include_router(wbs.router, prefix="/wbs", tags=["wbs"])
api_router.include_router(cost_codes.router, prefix="/cost-codes", tags=["cost-codes"])
api_router.include_router(boq.router, prefix="/boqs", tags=["boqs"])
api_router.include_router(estimates.router, prefix="/estimates", tags=["estimates"])
api_router.include_router(budgets.router, prefix="/budgets", tags=["budgets"])
api_router.include_router(suppliers.router, prefix="/suppliers", tags=["suppliers"])
api_router.include_router(requisitions.router, prefix="/requisitions", tags=["requisitions"])
api_router.include_router(rfqs.router, prefix="/rfqs", tags=["rfqs"])
api_router.include_router(quotations.router, prefix="/quotations", tags=["quotations"])
api_router.include_router(purchase_orders.router, prefix="/purchase-orders", tags=["purchase-orders"])
api_router.include_router(inventory.router, prefix="/inventory", tags=["inventory"])
api_router.include_router(project_cost.router, prefix="/project-cost", tags=["project-cost"])
api_router.include_router(accounting.router, prefix="/accounting", tags=["accounting"])
api_router.include_router(ap.router, prefix="/ap", tags=["ap"])
api_router.include_router(ar.router, prefix="/ar", tags=["ar"])
api_router.include_router(bank.router, prefix="/bank", tags=["bank"])
api_router.include_router(commercial.router, prefix="/commercial", tags=["commercial"])
api_router.include_router(hr.router, prefix="/hr", tags=["hr"])
api_router.include_router(equipment.router, prefix="/equipment", tags=["equipment"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(approvals.router, prefix="/approvals", tags=["approvals"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
