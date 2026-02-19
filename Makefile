install:
	uv sync

update:
	rm uv.lock
	uv sync

run-dev:
	uv run mcp dev main.py
