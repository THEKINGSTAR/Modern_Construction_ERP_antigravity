"""
app.models — Auto-registration of all SQLAlchemy ORM models.
Ensures that all domain models, foreign keys, and relationships are cleanly
discovered by SQLAlchemy Base.metadata across both testing and runtime.
"""

from app.models import accounting
from app.models import ap_ar
from app.models import approvals
from app.models import auth
from app.models import bank
from app.models import boq
from app.models import branch
from app.models import budgets
from app.models import clients
from app.models import commercial
from app.models import contracts
from app.models import cost_codes
from app.models import dimensions
from app.models import documents
from app.models import equipment
from app.models import estimates
from app.models import events
from app.models import forecasts
from app.models import goods_receipts
from app.models import hr
from app.models import inventory
from app.models import inventory_adjustments
from app.models import inventory_transfers
from app.models import legal_entity
from app.models import material_issues
from app.models import materials
from app.models import notifications
from app.models import org_settings
from app.models import projects
from app.models import purchase_orders
from app.models import quotations
from app.models import requisitions
from app.models import rfqs
from app.models import suppliers
from app.models import tenant
from app.models import user
from app.models import warehouses
from app.models import wbs
