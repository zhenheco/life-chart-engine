#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
VENDOR_DIR="$ROOT/vendor"
BUILD_DIR="$ROOT/vendor/.iztro-build"
OUT="$ROOT/vendor/iztro.cjs"

if ! command -v npm >/dev/null 2>&1; then
  echo "error: npm not found; install Node.js/npm before building iztro bundle." >&2
  exit 1
fi

rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

echo "==> Installing pinned iztro bundle inputs into $BUILD_DIR"
(
  cd "$BUILD_DIR"
  cp "$VENDOR_DIR/package.json" "$VENDOR_DIR/package-lock.json" .
  npm ci
)

printf "%s\n" "module.exports = require('iztro');" > "$BUILD_DIR/entry.cjs"

echo "==> Bundling vendor/iztro.cjs"
(
  cd "$BUILD_DIR"
  ./node_modules/.bin/esbuild entry.cjs --bundle --platform=node --format=cjs --outfile="$OUT"
)

node - "$OUT" <<'NODE'
const bundle = require(process.argv[2]);
if (!bundle || !bundle.astro || typeof bundle.astro.bySolar !== 'function') {
  throw new Error('iztro bundle verification failed: astro.bySolar missing');
}
NODE

echo "OK - wrote $OUT"
