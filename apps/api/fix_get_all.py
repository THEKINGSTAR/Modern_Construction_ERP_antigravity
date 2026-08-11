import os

files = [
    'app/api/endpoints/contracts.py',
    'app/api/endpoints/wbs.py',
    'app/api/endpoints/cost_codes.py'
]

for file in files:
    with open(file, 'r') as f:
        content = f.read()
    
    # fix get_all(skip=skip, limit=limit)
    content = content.replace('repo.get_all(skip=skip, limit=limit)', 'repo.get_all()[skip : skip + limit]')
    # fix get_all(limit=10000)
    content = content.replace('repo.get_all(limit=10000)', 'repo.get_all()')
    
    with open(file, 'w') as f:
        f.write(content)
