#!/usr/bin/env bash
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export LIFE_VENV="${LIFE_VENV:-$HOME/.claude/skills/life/.venv}"

if [ ! -x "$LIFE_VENV/bin/python" ]; then
  echo "missing test venv python at $LIFE_VENV/bin/python" >&2
  exit 1
fi

run_and_assert() {
  local cmd_path="$1"
  local tmp_out
  tmp_out="$(mktemp)"

  set +e
  bash "$cmd_path" --json \
    --date 1990-06-15 --time 08:30 --tz 8 --lat 25.0 --lon 121.5 \
    --target 2025-01-01 >"$tmp_out"
  local status=$?
  set -e

  if [ "$status" -ne 0 ]; then
    echo "wrapper exited with status $status: $cmd_path" >&2
    cat "$tmp_out" >&2
    rm -f "$tmp_out"
    exit 1
  fi

  "$LIFE_VENV/bin/python" -c 'import json,sys; d=json.load(sys.stdin); assert d["ok"]; print("WRAPPER_OK")' <"$tmp_out"
  rm -f "$tmp_out"
}

run_and_assert "$REPO/bin/life-chart"

tmp_link_dir="$(mktemp -d)"
ln -s "$REPO/bin/life-chart" "$tmp_link_dir/life-chart"
run_and_assert "$tmp_link_dir/life-chart"
rm -rf "$tmp_link_dir"

echo "SYMLINK_OK"
