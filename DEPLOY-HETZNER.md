# Deploy HTTP Engine on Hetzner

Target: existing Hetzner host with Docker + Cloudflare Tunnel, sharing the box with Movo.

Host: `acejou@157.90.157.99`
Tunnel: `engine-life.aicycle.cc` → `127.0.0.1:8012`

## 1. Build

```bash
cd /home/acejou/life-chart-engine
git pull --ff-only
docker build -t life-engine:latest .
```

## 2. Run

Use a long random key. Store the same value in `life-web`. For routine redeploys, preserve the key from the existing container so the Worker does not need a secret rotation:

```bash
ENGINE_API_KEY="$(docker inspect life-engine \
  --format '{{range .Config.Env}}{{println .}}{{end}}' \
  | sed -n 's/^ENGINE_API_KEY=//p' | head -1)"
test -n "$ENGINE_API_KEY"
```

```bash
docker rm -f life-engine 2>/dev/null || true
docker run -d \
  --name life-engine \
  --restart unless-stopped \
  -p 127.0.0.1:8012:8000 \
  -e ENGINE_API_KEY="$ENGINE_API_KEY" \
  -e SENTRY_DSN="$SENTRY_DSN" \
  -e SENTRY_ENVIRONMENT=production \
  -e SENTRY_RELEASE="$(git rev-parse --short HEAD)" \
  life-engine:latest
```

Without `ENGINE_API_KEY`, the service is open. Do not expose it publicly that way.
Keep `SENTRY_DSN` in 1Password or the host secret store; do not write the raw DSN
into the repo or shell history. `SENTRY_ENVIRONMENT` and `SENTRY_RELEASE` are
non-secret runtime labels used to group engine exceptions in Sentry.

## 3. Tunnel

`engine-life.aicycle.cc` is served by the existing `cloudflared` systemd service.
Routine app deploys do not need DNS, Caddy, or firewall changes.

## 4. Verify

```bash
curl -fsS https://engine-life.aicycle.cc/health

ENGINE_AUTH_HEADER="$(printf '%s: %s' 'X-Engine-Key' "$ENGINE_API_KEY")"
curl -fsS https://engine-life.aicycle.cc/chart \
  -H 'Content-Type: application/json' \
  -H "$ENGINE_AUTH_HEADER" \
  -d '{"date":"1990-06-15","time":"08:30","tz":8,"lat":25.0,"lon":121.5,"gender":"女","target":"2025-01-01"}'
```

For the chart request, construct the `X-Engine-Key` request header at runtime
from `ENGINE_API_KEY` (shell env or secret manager). Use `printf` instead of
copying key values into docs, shell history, tickets, or logs.

## 5. life-web

Set the Worker backend to call the HTTPS endpoint and send the key:

```env
ENGINE_URL=https://engine-life.aicycle.cc/chart
ENGINE_API_KEY=<set in platform secret store>
```

The Worker request must include the `X-Engine-Key` header value sourced from
the configured `ENGINE_API_KEY` secret.

The HTTP response schema is the same `schema_version: "1.2"` JSON object documented in `AGENTS.md`.

**Deploy order is web-first-safe.** The `life-web` client now accepts the whole `1.x` family, and `mutagen` stays string-compatible (the `1.1` additions — `mutagenTyped`, `decadal.ageRange`, the `age` sub-object — are additive only). So deploying the engine `1.1` will not break an already-running web; either order is safe, web-first preferred.

## 6. Deploy-regression verification (after every rebuild)

After rebuilding/redeploying the container, run the platform-independent
regression marker from the repo checkout and keep the full output as evidence:

```bash
pytest -m deploy_regression -r s
```

- Requirement: **the 3 tests selected by the marker must all be passed, and
  none of those selected tests may be skipped**. `-r s` prints every skipped
  test — any skip among the selected tests means deploy drift and must be
  investigated, not waived. The bare command's summary line can still show
  one unrelated collection-time skip from `tests/test_mcp_server.py` (see
  below); that skip is outside the deploy contract — judge the requirement
  on the selected tests, or use the `--ignore` form below for a clean
  zero-skip summary line. Platform-gated byte-identity tests are
  deliberately NOT marked `deploy_regression`: they skip off their capture
  platform (e.g. on a Linux host), and a skip is no evidence about the
  deployed build — marking them would fake a green result.
- The marker covers the platform-independent contract: `/health`
  `schema_version`, the `POST /chart` success path deep-equal against
  `examples/sample-output.json`, and the `POST /synastry` response shape.
- One known collection-time skip is unrelated to the deploy contract:
  `tests/test_mcp_server.py` skips at import when the optional `[mcp]` extra
  is not installed (it never is in a base checkout/image). To get a clean
  zero-skip summary line, exclude it explicitly:

```bash
pytest -m deploy_regression -r s --ignore=tests/test_mcp_server.py
```

- Also verify from outside before life-web traffic may rely on
  `POST /synastry`: `curl https://engine-life.aicycle.cc/health` must return
  JSON containing `"schema_version": "1.2"` (the engine must serve
  `/synastry` BEFORE life-web goes live — otherwise existing paid synastry
  customers get 502/503).
