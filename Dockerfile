# Pin amd64: Hetzner is x86. Python 3.12 remains the verified runtime for this
# change; the old Python Zi Wei native dependency constraint can be revisited.
FROM --platform=linux/amd64 python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

WORKDIR /app

# nodejs: run the Zi Wei sidecar at runtime.
RUN apt-get update && apt-get install -y --no-install-recommends \
      ca-certificates nodejs \
 && rm -rf /var/lib/apt/lists/*
RUN node --version

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Verify the engine imports and runs in THIS image — turns a runtime 500 on the
# first /chart call into a build failure.
RUN python -c "from scripts.chart_engine import build_json; print('import OK')"
RUN python scripts/chart_engine.py --json \
      --name "Docker Test" --gender 女 --date 1990-06-15 --time 08:30 \
      --tz 8 --lat 25.0 --lon 121.5 --target 2025-01-01 >/dev/null

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health').status==200 else 1)"

CMD ["sh", "-c", "uvicorn server:app --host 0.0.0.0 --port ${PORT:-8000}"]
