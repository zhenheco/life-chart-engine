#!/usr/bin/env bash
# life-chart-engine — one-line installer.
#
#   curl -fsSL https://raw.githubusercontent.com/zhenheco/life-chart-engine/main/install.sh | bash
#
# Safe by design: no sudo, no system-wide changes. Clones into
# ~/.life-chart-engine (override with LIFE_CHART_DIR) and builds an isolated
# CPython 3.12 venv via uv. Re-running updates an existing install.
set -euo pipefail

REPO_URL="${LIFE_CHART_REPO:-https://github.com/zhenheco/life-chart-engine.git}"
DEST="${LIFE_CHART_DIR:-$HOME/.life-chart-engine}"

echo "==> life-chart-engine installer"

if ! command -v git >/dev/null 2>&1; then
  echo "error: 'git' is required but not found." >&2
  exit 1
fi
if ! command -v uv >/dev/null 2>&1; then
  echo "error: 'uv' is required but not found." >&2
  echo "  install uv: curl -LsSf https://astral.sh/uv/install.sh | sh" >&2
  echo "  then re-run this installer." >&2
  exit 1
fi

if [ -d "$DEST/.git" ]; then
  echo "==> Updating existing install at $DEST"
  git -C "$DEST" pull --ff-only
else
  echo "==> Cloning into $DEST"
  git clone --depth 1 "$REPO_URL" "$DEST"
fi

echo "==> Running setup (CPython 3.12 venv + dependencies)"
cd "$DEST"
bash setup.sh

cat <<EOF

==> Done. Installed at: $DEST

Compute a chart (human-readable):
  "$DEST/.venv/bin/python" "$DEST/scripts/chart_engine.py" --help

Machine-readable (for AI agents), add --json. See:
  $DEST/AGENTS.md
EOF
