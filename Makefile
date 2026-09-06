.PHONY: bootstrap validate status test test-agent clean

bootstrap:
	python3 scripts/agent.py bootstrap

validate:
	python3 scripts/agent.py validate

status:
	python3 scripts/agent.py status

test:
	bash scripts/test.sh

test-agent:
	python3 scripts/agent.py simulate-tests

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
