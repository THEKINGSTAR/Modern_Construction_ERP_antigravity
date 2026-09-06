# LES-002: Circular Foreign Key Constraints & SQLite Test Teardown

## Category
Database / Testing / ORM

## Root Cause
In `apps/api/app/models/hr.py`, `HRDepartment` references `Employee` (manager) and `Employee` references `HRDepartment`. During pytest teardown, SQLite fails when dropping tables or altering constraints if foreign keys are circular without explicit deferred teardown directives.

## Rule / Invariant
- Circular foreign key relationships in SQLAlchemy models MUST declare `use_alter=True` and a unique constraint name on one side of the relationship (e.g. `ForeignKey('employees.id', use_alter=True, name='fk_hr_department_manager_id')`).
- Tests run against in-memory SQLite (`sqlite:///:memory:`). Never use PostgreSQL-only syntax without ensuring SQLite test compatibility.
