from decimal import Decimal
from typing import Dict, Any

class PaymentCalculationEngine:
    """
    Stateless engine to calculate payment applications.
    Calculation:
    Gross Work
    - Previous Certified Work
    - Retention
    - Advance Recovery
    - Approved Deductions
    +/- Adjustments
    = Net Amount Due
    """
    
    @staticmethod
    def calculate_net_amount_due(
        gross_work: Decimal,
        previous_certified_work: Decimal,
        retention_amount: Decimal,
        advance_recovery_amount: Decimal,
        deductions_amount: Decimal,
        adjustments_amount: Decimal
    ) -> Decimal:
        
        # Current certified work in this period
        current_certified_work = gross_work - previous_certified_work
        if current_certified_work < Decimal("0.0"):
            raise ValueError(f"Gross work ({gross_work}) cannot be less than previous certified work ({previous_certified_work}).")
            
        net_amount_due = (
            current_certified_work
            - retention_amount
            - advance_recovery_amount
            - deductions_amount
            + adjustments_amount
        )
        
        # If the result is negative, it implies the subcontractor/client owes us money in this period,
        # which can happen if deductions are massive, but typically it should be flagged or handled.
        # We will allow it for now mathematically but a business rule might constrain this.
        return net_amount_due

    @staticmethod
    def calculate_retention(
        gross_work: Decimal,
        retention_rate: Decimal
    ) -> Decimal:
        """
        Calculates simple retention based on gross work and retention rate.
        Retention limits can be implemented here in the future.
        """
        if retention_rate < Decimal("0.0") or retention_rate > Decimal("100.0"):
            raise ValueError("Retention rate must be between 0 and 100.")
            
        rate_fraction = retention_rate / Decimal("100.0")
        return gross_work * rate_fraction
