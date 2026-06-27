# Deploy HTTP Engine on Hetzner

Target: existing Hetzner host with Docker + Caddy, sharing the box with Movo.

## 1. Build

```bash
cd /home/acejou/life-chart-engine
git pull --ff-only
docker build -t life-engine:latest .
```

## 2. Run

Use a long random key. Store the same value in `life-web`.

```bash
docker rm -f life-engine 2>/dev/null || true
docker run -d \
  --name life-engine \
  --restart unless-stopped \
  -p 127.0.0.1:8012:8000 \
  -e ENGINE_API_KEY='replace-with-long-random-key' \
  life-engine:latest
```

Without `ENGINE_API_KEY`, the service is open. Do not expose it publicly that way.

## 3. Caddy

Add this site block to the Caddyfile:

```caddyfile
engine-life.aicycle.cc {
	reverse_proxy 127.0.0.1:8012
}
```

Reload Caddy:

```bash
caddy fmt --overwrite /etc/caddy/Caddyfile
systemctl reload caddy
```

Caddy terminates HTTPS for `engine-life.aicycle.cc` and proxies to the local container.

## 4. Verify

```bash
curl -fsS https://engine-life.aicycle.cc/health

curl -fsS https://engine-life.aicycle.cc/chart \
  -H 'Content-Type: application/json' \
  -H 'X-Engine-Key: replace-with-long-random-key' \
  -d '{"date":"1990-06-15","time":"08:30","tz":8,"lat":25.0,"lon":121.5,"gender":"女","target":"2025-01-01"}'
```

## 5. life-web

Set the Worker backend to call the HTTPS endpoint and send the key:

```env
ENGINE_URL=https://engine-life.aicycle.cc/chart
ENGINE_API_KEY=replace-with-long-random-key
```

The Worker request must include:

```http
X-Engine-Key: replace-with-long-random-key
```

The HTTP response schema is the same `schema_version: "1.1"` JSON object documented in `AGENTS.md`.

**Deploy order is web-first-safe.** The `life-web` client now accepts the whole `1.x` family, and `mutagen` stays string-compatible (the `1.1` additions — `mutagenTyped`, `decadal.ageRange`, the `age` sub-object — are additive only). So deploying the engine `1.1` will not break an already-running web; either order is safe, web-first preferred.
