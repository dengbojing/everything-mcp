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
on Windows for branch pushes and pull requests. A push to `master` in the original
repository also publishes the checked artifacts to PyPI if the version's `v*`
tag does not exist. After publishing succeeds, it creates that tag at the tested
commit and a GitHub Release with generated notes and the wheel/source archives.
PRs and other branches never publish. Only stable public versions are automated.
The separate Linux publishing job uploads artifacts; it does not run Everything.
No local publishing script or long-lived PyPI token is required.

One-time setup:

1. In the GitHub repository settings, create an environment named `pypi`.
   Allow deployment from the `master` branch (not only `v*` tags); enable required
   reviewers if available. Update this rule if you used the old tag workflow.
2. In PyPI, configure a GitHub Trusted Publisher. For a new project, use a pending
   publisher at https://pypi.org/manage/account/publishing/ with:
   - PyPI project: `evryth-mcp`
   - Owner: `dengbojing`
   - Repository: `everything-mcp`
   - Workflow filename: `publish.yml`
   - Environment: `pypi`
   For an existing project, add the publisher in its publishing settings.
3. Protect `master` and release tags. Ensure repository rules permit the workflow's
   `GITHUB_TOKEN` to create release tags; only the release job has `contents: write`.

To release, update `project.version` in `pyproject.toml`, run `uv lock`, and commit
and push the changes to `master`:

```powershell
git push origin master
```

Use a new version for each release; published distribution filenames cannot be
reused. Configure the PyPI publisher before pushing an untagged version to master.
Do not create tags manually: an existing version tag skips automatic publishing.
If PyPI succeeds but the release job fails, rerun only the failed job in the same
Actions run; do not rebuild and re-upload the published version. If a partial
GitHub Release already exists, inspect and complete it manually before retrying.
Branch runs are serialized; GitHub may replace older pending runs with newer ones.
If the repository is renamed, update both the workflow repository guard and PyPI
publisher settings.

Reference: https://docs.pypi.org/trusted-publishers/using-a-publisher/
