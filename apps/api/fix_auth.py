import os

files = [
    'app/api/endpoints/contracts.py',
    'app/api/endpoints/wbs.py',
    'app/api/endpoints/cost_codes.py'
]

for file in files:
    with open(file, 'r') as f:
        content = f.read()
    
    # fix imports
    content = content.replace('from app.core.security import require_permission', 'from app.core.auth import require_permissions')
    
    import re
    # fix require_permission("...") to require_permissions(["..."])
    content = re.sub(r'require_permission\("([^"]+)"\)', r'require_permissions(["\1"])', content)
    
    with open(file, 'w') as f:
        f.write(content)
