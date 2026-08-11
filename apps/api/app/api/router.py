from fastapi import APIRouter
from app.api.endpoints import auth, settings, clients, projects, contracts, wbs, cost_codes, boq, estimates, budgets

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(settings.router, prefix="/settings", tags=["settings"])
api_router.include_router(clients.router, prefix="/clients", tags=["clients"])
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(contracts.router, prefix="/contracts", tags=["contracts"])
api_router.include_router(wbs.router, prefix="/wbs", tags=["wbs"])
api_router.include_router(cost_codes.router, prefix="/cost-codes", tags=["cost-codes"])
api_router.include_router(boq.router, prefix="/boqs", tags=["BOQ"])
api_router.include_router(estimates.router, prefix="/estimates", tags=["Estimates"])
api_router.include_router(budgets.router, prefix="/budgets", tags=["Budgets"])
