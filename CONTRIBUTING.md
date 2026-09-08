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
`evryth-mcp` and `python -m everything_mcp` start the STDIO server.

Live integration requires Windows, an accessible Everything IPC instance,
and the sample file asserted in tests/integration.py:

```powershell
uv run python -m tests.integration
```

Live integration is excluded from normal discovery. Adjust the fixed sample
before using a different machine. Never emit diagnostics on protocol stdout.
Changes to public tool names or schemas require explicit compatibility review.

## GitHub Actions and PyPI

`.github/workflows/publish.yml` runs offline tests, Ruff, and distribution checks
on Windows for branch pushes and pull requests. A `v*` tag also publishes the
checked artifacts to PyPI, only when the tag matches the project version exactly.
The separate Linux publishing job uploads artifacts; it does not run Everything.
No local publishing script or long-lived PyPI token is required.

One-time setup:

1. In the GitHub repository settings, create an environment named `pypi`.
   Restrict deployment tags to `v*`; enable required reviewers if available.
2. In PyPI, configure a GitHub Trusted Publisher. For a new project, use a pending
   publisher at https://pypi.org/manage/account/publishing/ with:
   - PyPI project: `evryth-mcp`
   - Owner: `dengbojing`
   - Repository: `everything-mcp`
   - Workflow filename: `publish.yml`
   - Environment: `pypi`
   For an existing project, add the publisher in its publishing settings.
3. Protect release tags in GitHub so only authorized maintainers can create them.

To release, update `project.version` in `pyproject.toml`, run `uv lock`, and commit
and push the changes. Then push a matching tag, for example for version `0.1.0`:

```powershell
git tag v0.1.0
git push origin v0.1.0
```

Use a new version for each release; published distribution filenames cannot be
reused. Do not push a release tag until the PyPI publisher is configured.
If the repository is renamed, update both the workflow repository guard and PyPI
publisher settings.

Reference: https://docs.pypi.org/trusted-publishers/using-a-publisher/
