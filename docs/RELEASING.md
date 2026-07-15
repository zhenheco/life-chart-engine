# Releasing life-chart-engine

Releases are built by `.github/workflows/publish.yml` and uploaded to PyPI with
Trusted Publishing. The workflow runs only when a GitHub Release changes to
`published`; saving a draft does not publish a package.

## One-time publisher setup

Complete this before publishing the first GitHub Release. Publishing the
release starts the upload immediately, and a PyPI pending publisher does not
reserve the project name until that first upload succeeds.

1. In the GitHub repository, open **Settings → Environments → New environment**
   and create an environment named exactly `pypi`. Add required reviewers so a
   maintainer must approve the publish job.
2. Sign in to PyPI and open **Account settings → Publishing → Add a new pending
   publisher**.
3. Choose **GitHub Actions** and enter these values:

   | Field | Value |
   |---|---|
   | PyPI project name | `life-chart-engine` |
   | Owner | `zhenheco` |
   | Repository name | `life-chart-engine` |
   | Workflow name | `publish.yml` |
   | Environment name | `pypi` |

4. Select **Add**. Keep the publisher pending until the first release workflow
   succeeds; PyPI converts it to a normal Trusted Publisher automatically.

If `life-chart-engine` already exists on PyPI, do not create a pending
publisher. Open that project's **Manage → Publishing** page and add the same
GitHub Actions publisher there instead. The owner, repository, workflow, and
environment values on PyPI must exactly match the workflow's OIDC claims.

No PyPI API token, username, password, or GitHub publishing secret is needed.

## Release checklist

Use CPython 3.12 and Node.js 18 or newer. Start from an up-to-date `main` branch
with a clean working tree.

1. Set the release version in `pyproject.toml` under `[project].version`. Keep
   the Git tag in the form `v<version>`; for example, package version `1.1.0`
   uses tag `v1.1.0`.
2. Run the release checks:

   ```bash
   VERSION=1.1.0
   export LIFE_VENV="$(pwd)/.venv"
   test -x "$LIFE_VENV/bin/python" || bash setup.sh
   uv pip install --python "$LIFE_VENV/bin/python" -r requirements-dev.txt
   RELEASE_DIST="$(mktemp -d)"
   trap 'rm -rf "$RELEASE_DIST"' EXIT
   .venv/bin/python -m pytest tests/ -x -q
   .venv/bin/python -m build --outdir "$RELEASE_DIST"
   .venv/bin/python -m twine check "$RELEASE_DIST"/*
   ```

3. Commit the version bump, create an annotated tag on that commit, and push
   both the commit and tag:

   ```bash
   git add pyproject.toml
   git commit -m "chore(release): v${VERSION}"
   git tag -a "v${VERSION}" -m "life-chart-engine v${VERSION}"
   git push origin main
   git push origin "v${VERSION}"
   ```

4. On GitHub, open **Releases → Draft a new release**, select the pushed tag,
   add the release notes, and review the draft. Confirm the tagged commit
   contains `.github/workflows/publish.yml` and the intended version bump.
5. Select **Publish release** once. This fires the `release: published`
   workflow, which builds and checks the wheel and source distribution before
   the separate OIDC publish job uploads them to PyPI.
6. Confirm both workflow jobs are green and the new version appears at
   <https://pypi.org/project/life-chart-engine/>. Then verify both public entry
   points from outside this checkout:

   ```bash
   uvx "life-chart-engine@${VERSION}" --example --json
   uvx --from "life-chart-engine==${VERSION}" life-chart --example --json
   ```

Do not delete and recreate a published GitHub Release to retry a failed upload.
First inspect the project on PyPI. If no distribution file was accepted, fix
the cause and re-run the failed workflow job. If PyPI accepted any file, do not
reuse that filename; resolve the problem and cut a new package version because
PyPI distribution files are immutable.

## Dependency and install-path notes

- The MCP extra is intentionally pinned to `mcp==1.28.1`. Before every release,
  confirm the exact pin in `pyproject.toml` still matches this document. Any MCP
  upgrade requires compatibility testing before changing both values together.
- The repository's `install.sh` always installs `~/.local/bin/life-chart`. For
  `pip install --user life-chart-engine`, scripts are installed in
  `$(python -m site --user-base)/bin`: this is typically `~/.local/bin` on Linux
  and with uv/pyenv CPython, but `~/Library/Python/<version>/bin` with macOS
  framework builds. The two methods overwrite each other only when they target
  the same directory. Prefer one installation method, or use `uvx`.
