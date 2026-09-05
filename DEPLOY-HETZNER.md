# Self-hosting the HTTP engine (Docker)

Runs the engine as a container on any Linux host with Docker, bound to
localhost and exposed through a reverse proxy or tunnel of your choice
(the reference deployment uses a Cloudflare Tunnel, so the host opens no
inbound ports).

> Operator note: host addresses, credentials, and rollback state for the
> reference deployment are kept in a private runbook, not in this repo.

## 1. Build

```bash
cd /path/to/life-chart-engine
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

**Deploy order is web-first-safe.** The `life-web` client now accepts the whole `1.x` family, and `mutagen` stays string-compatible (the `1.1` additions — `mutagenTyped`, `decadal.ageRange`, the `age` sub-object — are additive only). So deploying the engine `1.2` will not break an already-running web; either order is safe, web-first preferred.

## 6. Deploy-regression verification (after every rebuild)

After rebuilding/redeploying the container, run BOTH layers below and keep the
full output of each as evidence. They answer different questions — one without
the other gives false confidence.

### 6a. Source-contract regression (in this checkout)

Run the platform-independent regression marker from the repo checkout:

```bash
pytest -m deploy_regression -r s
```

**Capability boundary — read before trusting a green result:** the marker
executes `TestClient(server.app)` **inside this checkout**, so it proves
"this source code honours the contract". It does **NOT** prove "the deployed
container is serving this code" — it never touches the container, and `pytest`
is a dev-only dependency that is not inside the image. A stale image or a
wrong deploy still passes 6a; only layer 6b catches that drift.

- Requirement: **the 3 tests selected by the marker must all be passed, and
  none of those selected tests may be skipped**. `-r s` prints every skipped
  test — any skip among the selected tests means the contract is broken and
  must be investigated, not waived. The bare command's summary line can still
  show one unrelated collection-time skip from `tests/test_mcp_server.py`
  (see below); that skip is outside the deploy contract — judge the
  requirement on the selected tests, or use the `--ignore` form below for a
  clean zero-skip summary line. Platform-gated byte-identity tests are
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

### 6b. Live-container verification (against the deployed host)

This is the only layer that actually touches the deployed container — the one
that catches "an older build is still being served" drift. From the repo
checkout, POST the pinned sample inputs to the live host and keep the
responses as evidence.

Reuse the `ENGINE_AUTH_HEADER` built in §4 so the key value never appears
inline in this document or in shell history. The variable only exists if §2
and §4 ran in this same shell — assert it before POSTing, so a fresh shell
fails loudly instead of expanding to an empty header and sending the request
unauthenticated:

```bash
test -n "$ENGINE_AUTH_HEADER" && \
curl -fsS -X POST https://engine-life.aicycle.cc/chart \
  -H "$ENGINE_AUTH_HEADER" -H 'content-type: application/json' \
  -d @examples/sample-input.json > /tmp/live-chart.json
```

The `&&` is load-bearing: pasted as two separate statements into an
interactive shell (no `set -e`), a failing `test` would not stop the `curl`
below it, and the request would go out with an empty auth header.

`-f` makes curl exit non-zero WITHOUT writing a body on HTTP errors
(401/502/503). Without it, the error body lands in `/tmp/live-chart.json`
and the next step misreports an auth or proxy failure as "deploy drift",
pointing the investigation at the wrong cause.

Then compare the live response against the pinned golden output. The
`schema_version` check is an assertion inside the comparison, not prose next
to it: the only diff between the pre-1.2 golden and this checkout's golden
is that one line, so a stale build still serving the old value must fail the
check rather than pass it:

```bash
python3 - <<'PY'
import json
live = json.load(open("/tmp/live-chart.json"))
sample = json.load(open("examples/sample-output.json"))
live_sv = live.get("schema_version")
assert live_sv == "1.2", (
    f"deploy drift: live schema_version is {live_sv!r}, expected '1.2'"
)
live.pop("schema_version", None)
sample.pop("schema_version", None)
assert live == sample, (
    "deploy drift: live /chart output differs from examples/sample-output.json"
)
print("live /chart deep-equal against examples/sample-output.json: OK")
PY
```

`examples/sample-input.json` is the exact request body that produces
`examples/sample-output.json` (the `deploy_regression` chart test posts the
same fixture). Any mismatch here means the container is NOT serving this
checkout's code — investigate the image/tag, never waive. Keep
`/tmp/live-chart.json` with the deploy evidence.

Also smoke `POST /synastry` against the live host — a missing or failing
`/synastry` is exactly what hands existing paid synastry customers 502/503
once life-web goes live, so the endpoint must be serving BEFORE that rollout:

```bash
test -n "$ENGINE_AUTH_HEADER" && \
curl -fsS -X POST https://engine-life.aicycle.cc/synastry \
  -H "$ENGINE_AUTH_HEADER" -H 'content-type: application/json' \
  -d @examples/sample-synastry-input.json > /tmp/live-synastry.json
python3 - <<'PY'
import json
live = json.load(open("/tmp/live-synastry.json"))
assert live["ok"] is True, "deploy drift: live /synastry did not return ok=true"
assert "evidence_completeness" in live, (
    "deploy drift: live /synastry response lacks evidence_completeness"
)
print("live /synastry smoke: OK")
PY
```

`examples/sample-synastry-input.json` is the same two-person body the
`deploy_regression` synastry shape test posts. Keep `/tmp/live-synastry.json`
with the deploy evidence. As a final outside check,
`curl https://engine-life.aicycle.cc/health` must return JSON containing
`"schema_version": "1.2"`.

## 7. Per-IP rate limiting (NOT applied yet — ops task on the host)

`ENGINE_API_KEY` and the `LIFE_MAX_BODY_BYTES` request-size cap (server.py,
default 64 KiB) are the only request-shedding controls the Python service
implements. Per-IP request-rate limiting is deliberately **not** implemented
in Python — it belongs at the reverse-proxy/edge layer in front of the
container, where it can reject abusive traffic before it reaches the process.
**This has not been configured on the reference Hetzner host as of this
writing.**

The reference deployment fronts the container with a Cloudflare Tunnel
(`cloudflared`, see §3), not a locally-run Caddy/nginx. Cloudflare's own edge
(WAF rate limiting rules on the zone) is the natural place to add this for
that specific topology. If a local reverse proxy sits in front of the
container instead (or is added later), concrete config to adapt:

**Caddy** (`rate_limit` via the `caddy-ratelimit` plugin — not built into
core Caddy, must be added at build time):

```
engine-life.aicycle.cc {
	rate_limit {
		zone engine_per_ip {
			key {remote_host}
			events 60
			window 1m
		}
	}
	reverse_proxy 127.0.0.1:8012
}
```

**nginx** (`limit_req`, built in):

```nginx
limit_req_zone $binary_remote_addr zone=engine_per_ip:10m rate=60r/m;

server {
    listen 443 ssl;
    server_name engine-life.aicycle.cc;

    location / {
        limit_req zone=engine_per_ip burst=20 nodelay;
        proxy_pass http://127.0.0.1:8012;
    }
}
```

Either snippet caps at ~60 requests/minute/IP as a starting point — tune to
the actual `life-web` call volume before relying on it. Whichever layer is
chosen, verify it actually rejects with a `429` under load before treating
this section as done; an unapplied snippet in a doc is not a mitigation.
