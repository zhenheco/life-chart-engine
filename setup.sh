#!/usr/bin/env bash
# life-chart-engine setup — create a CPython 3.12 venv and install dependencies.
#
# WHY 3.12: py-iztro's native deps (pythonmonkey / pydantic-core) have no wheels
# for newer Pythons (3.13+/3.14) and fail to build from source. Pin to 3.12.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="${LIFE_VENV:-$HERE/.venv}"

if ! command -v uv >/dev/null 2>&1; then
  echo "error: 'uv' not found." >&2
  echo "  install: curl -LsSf https://astral.sh/uv/install.sh | sh" >&2
  echo "  docs:    https://docs.astral.sh/uv/" >&2
  exit 1
fi

echo "==> Creating venv (CPython 3.12) at $VENV"
uv venv --python 3.12 "$VENV"

echo "==> Installing dependencies"
uv pip install --python "$VENV/bin/python" -r "$HERE/requirements.txt"

echo "==> Smoke test"
"$VENV/bin/python" "$HERE/scripts/chart_engine.py" --json \
  --name "Setup Test" --gender 女 --date 1990-06-15 --time 08:30 \
  --tz 8 --lat 25.0 --lon 121.5 --target 2025-01-01 >/dev/null \
  && echo "OK — engine runs."
echo
echo "Run a chart (human-readable Markdown):"
echo "  $VENV/bin/python scripts/chart_engine.py --name 你的名字 --gender 女 \\"
echo "    --date 1990-06-15 --time 08:30 --tz 8 --lat 25.0 --lon 121.5"
echo "After install.sh, the PATH shortcut is available as: life-chart --help"
echo "Add --json for machine-readable output (see AGENTS.md)."
