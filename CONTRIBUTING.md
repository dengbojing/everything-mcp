# Development

## Layout

- src/everything_mcp/server.py: MCP registration and application entry point.
- src/everything_mcp/service.py: search use cases and result assembly.
- src/everything_mcp/es.py: subprocess and IPC error boundary.
- src/everything_mcp/query.py: ES argument validation and expressions.
- src/everything_mcp/models.py: validated public filters and parameter types.
- src/everything_mcp/matching.py: pinyin matching algorithm.
- tests/: offline unit/contract tests and opt-in live integration.

## Checks

```powershell
uv sync --locked
uv run ruff check src tests
uv run ruff format --check src tests
uv run python -m unittest discover -v
uv build
```

The src layout requires installing the project before importing it. Both
`everything-mcp` and `python -m everything_mcp` start the STDIO server.

Live integration requires Windows, an accessible Everything IPC instance,
and the sample file asserted in tests/integration.py:

```powershell
uv run python -m tests.integration
```

Live integration is excluded from normal discovery. Adjust the fixed sample
before using a different machine. Never emit diagnostics on protocol stdout.
Changes to public tool names or schemas require explicit compatibility review.
