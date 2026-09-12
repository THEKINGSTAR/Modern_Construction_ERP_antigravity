from uuid import UUID
from decimal import Decimal
from typing import Optional
from sqlalchemy.orm import Session
from app.services.project_cost import ProjectCostEngine

class BudgetProjectionService:
    """
    Service responsible for rolling up Committed Costs, Actual Costs, and Forecast Costs
    for a given budget line by querying the ProjectCostEngine.
    """
    
    @staticmethod
    def get_committed_cost(project_id: UUID, cost_code_id: UUID, tenant_id: UUID, db: Optional[Session] = None) -> Decimal:
        if db is None:
            from app.core.database import SessionLocal
            session = SessionLocal()
            close_session = True
        else:
            session = db
            close_session = False
        try:
            engine = ProjectCostEngine(session, tenant_id)
            summaries = engine.get_project_cost_summary(project_id)
            for s in summaries:
                if s.cost_code_id == cost_code_id:
                    return s.committed_cost
            return Decimal("0.00")
        finally:
            if close_session:
                session.close()

    @staticmethod
    def get_actual_cost(project_id: UUID, cost_code_id: UUID, tenant_id: UUID, db: Optional[Session] = None) -> Decimal:
        if db is None:
            from app.core.database import SessionLocal
            session = SessionLocal()
            close_session = True
        else:
            session = db
            close_session = False
        try:
            engine = ProjectCostEngine(session, tenant_id)
            summaries = engine.get_project_cost_summary(project_id)
            for s in summaries:
                if s.cost_code_id == cost_code_id:
                    return s.actual_cost
            return Decimal("0.00")
        finally:
            if close_session:
                session.close()

    @staticmethod
    def get_forecast_cost(project_id: UUID, cost_code_id: UUID, tenant_id: UUID, db: Optional[Session] = None) -> Decimal:
        if db is None:
            from app.core.database import SessionLocal
            session = SessionLocal()
            close_session = True
        else:
            session = db
            close_session = False
        try:
            engine = ProjectCostEngine(session, tenant_id)
            summaries = engine.get_project_cost_summary(project_id)
            for s in summaries:
                if s.cost_code_id == cost_code_id:
                    return s.estimate_at_completion
            return Decimal("0.00")
        finally:
            if close_session:
                session.close()
