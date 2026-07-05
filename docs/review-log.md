# Review Log

## 2026-07-05 - Dependency Audit Closure

- Scope: local dependency/security follow-up for the active 30-day portfolio audit.
- Fixed: upgraded `fastapi` from `0.128.8` to `0.139.0` and pinned FastAPI's Starlette runtime dependency to `starlette==1.3.1`, closing `pip-audit` findings against `starlette==0.52.1` (`PYSEC-2026-161`, `PYSEC-2026-249`, `PYSEC-2026-248`, `CVE-2026-48818`, `CVE-2026-48817`).
- Fixed: added `pytest==9.1.1` to `requirements-dev.txt` so the documented pytest gate is reproducible in a fresh dev/audit venv.
- Fixed: added `requirements.lock` from `uv pip compile --python-version 3.12 requirements.txt requirements-dev.txt -o requirements.lock` so the audited transitive set is reproducible.
- Verified in an isolated CPython 3.12.13 venv under `/tmp`:
  - `uv pip install --python "$tmp/.venv/bin/python" -r requirements.txt -r requirements-dev.txt`
  - package metadata check: `fastapi==0.139.0` declares `Requires-Dist: starlette>=0.46.0`; `starlette==1.3.1` resolves without overriding FastAPI's declared constraints.
  - `uvx pip-audit --path "$tmp/.venv/lib/python3.12/site-packages" --progress-spinner off`: no known vulnerabilities found.
  - `"$tmp/.venv/bin/python" -m pytest -q`: 40 passed, 1 Starlette TestClient deprecation warning.
  - `uvx --from ruff==0.15.20 ruff check .`: passed.
- Verified secrets posture: `gitleaks dir . --redact --no-banner` and `gitleaks detect --source . --log-opts origin/main..HEAD --redact --no-banner` reported no leaks.
- Not performed: production deploy, live engine smoke, host secret-store access, Sentry provider/dashboard operations, raw secret reads, secret rotation, dependency auto-fix, or git history rewrite.

## 2026-07-01 - Security Audit Remediation

- Scope: local source remediation for `webapp.py`, `DEPLOY-HETZNER.md`, and security regression tests.
- Fixed: webapp DOM XSS risk from dynamic chart/input values rendered through `innerHTML`; browser rendering now uses `textContent`, DOM node construction, and `replaceChildren`.
- Fixed: deploy verification docs now build the engine auth header from `ENGINE_API_KEY` at runtime with `printf`, then pass `-H "$ENGINE_AUTH_HEADER"` instead of embedding a literal key-bearing header snippet.
- Fixed: added a Python lint gate with `ruff` pyflakes rules and removed the unused Human Design `psun` assignment it surfaced.
- Verified:
  - `.venv/bin/python -m pytest tests/test_webapp_dom_safety.py -q`
  - `uvx --from ruff==0.15.20 ruff check .`
  - `.venv/bin/python -m pytest -q`
  - `gitleaks detect --source . --redact --no-banner --no-git`
  - `git diff --check`
- Disposition: the current tree is clean for the local remediation scope.
- Owner-gated: full-history gitleaks still reports historical redacted fingerprint `c06bccdce17001b1f0e36144b6c7beefd69ddcb1:DEPLOY-HETZNER.md:curl-auth-header:51`; it is an env-var header example, not a current raw secret, and history/allowlist/rotation policy remains owner-gated.
- Not performed: production deploy, live engine smoke, host secret-store access, Sentry provider/dashboard operations, raw secret reads, secret rotation, or git history rewrite.
