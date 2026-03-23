install:
	uv sync --all-extras

update:
	rm uv.lock
	uv sync

lint:
	uv run ruff check .

fix:
	uv run ruff check . --fix

format:
	uv run ruff format .

check: format fix

run-dev:
	uv run mcp dev src/datashield_mcp/server.py

run-stdio:
	uv run datashield-mcp

run-http:
	uv run datashield-mcp --transport streamable-http --host 127.0.0.1 --port 8000

test:
	uv run pytest -vv src/tests
