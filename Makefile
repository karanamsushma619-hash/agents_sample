.PHONY: format lint test

format:
	black src tests apps
	ruff check --fix src tests apps

lint:
	ruff check src tests apps

test:
	pytest
