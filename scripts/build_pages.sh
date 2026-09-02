#!/usr/bin/env bash
# Build a Flask-free static preview for GitHub Pages.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEST="${1:-"$ROOT/_site"}"

rm -rf "$DEST"
mkdir -p "$DEST"

cp "$ROOT/static-preview/index.html" "$DEST/index.html"
cp "$ROOT/state.sample.json" "$DEST/state.json"
cp "$ROOT/frontend/office_bg_small.webp" "$DEST/office_bg_small.webp"
cp "$ROOT/frontend/desk-v3.webp" "$DEST/desk-v3.webp"
cp "$ROOT/frontend/fonts/ark-pixel-12px-proportional-ja.ttf.woff2" "$DEST/ark-pixel.woff2"
touch "$DEST/.nojekyll"

echo "Built static preview at $DEST"
