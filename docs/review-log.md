# Review Log

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
