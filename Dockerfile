# Pin amd64: Hetzner is x86, and py-iztro's native deps (pythonmonkey, pydantic-core)
# only ship manylinux wheels for amd64 — on arm64 pip compiles from source.
FROM --platform=linux/amd64 python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

WORKDIR /app

# build-essential: compile pyswisseph. nodejs+npm: py-iztro's pythonmonkey dep
# builds `pminit`, whose post-install hook shells out to npm (fails without it).
# libstdc++6/libffi8: runtime libs the SpiderMonkey .so dynamically links.
RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential libstdc++6 libffi8 ca-certificates nodejs npm \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Verify the native deps actually import in THIS image — turns a runtime 500 on
# the first /chart call into a build failure.
RUN python -c "from scripts.chart_engine import build_json; print('import OK')"

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health').status==200 else 1)"

CMD ["sh", "-c", "uvicorn server:app --host 0.0.0.0 --port ${PORT:-8000}"]
