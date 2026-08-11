import re

with open('migrations/versions/c34280f7c043_procurement_auto.py', 'r') as f:
    lines = f.readlines()

new_lines = []
skip = False
for line in lines:
    if 'op.alter_column(' in line or 'op.drop_column(' in line or 'op.add_column(' in line or 'op.create_foreign_key(None' in line or 'op.drop_constraint(None' in line or 'op.create_index(op.f(''ix_accounting_periods_tenant_id' in line or 'op.create_index(op.f(''ix_exchange_rates_tenant_id' in line or 'op.create_index(op.f(''ix_fiscal_years_tenant_id' in line or 'op.create_index(op.f(''ix_tenant_settings_tenant_id' in line or 'op.drop_index(op.f(''ix_tenant_settings_tenant_id' in line or 'op.drop_index(op.f(''ix_fiscal_years_tenant_id' in line or 'op.drop_index(op.f(''ix_exchange_rates_tenant_id' in line or 'op.drop_index(op.f(''ix_accounting_periods_tenant_id' in line:
        skip = True
    
    if skip:
        if line.strip() == 'existing_nullable=False)' or line.strip() == 'existing_nullable=True)' or line.strip() == 'existing_nullable=True))' or line.strip() == 'existing_nullable=False))' or ')' in line and 'existing_nullable' in line:
            skip = False
            continue
        if ')' in line and not 'op.' in line and skip and not line.strip().startswith('type_='):
            # some other end parenthesis
            if 'ondelete' in line or 'existing_type' in line or 'type_=' in line:
                pass
            else:
                skip = False
                continue
        continue
        
    new_lines.append(line)

with open('migrations/versions/c34280f7c043_procurement_auto.py', 'w') as f:
    f.writelines(new_lines)
