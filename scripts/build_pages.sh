#!/usr/bin/env bash
# Build the current public office for GitHub Pages project URL
# https://rezent011-sketch.github.io/saiyan-office/
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEST="${1:-"$ROOT/_site"}"

export PUBLIC_OFFICE_DEST="$DEST"
# Project Pages URL is /saiyan-office/; use relative asset paths so
# static/foo resolves to /saiyan-office/static/foo, not the user-site root.
export PUBLIC_ASSET_PREFIX=""
export PUBLIC_RELATIVE_ASSETS=1
export PUBLIC_WRITE_CNAME=0
export PUBLIC_OFFICE_API_ORIGIN="${PUBLIC_OFFICE_API_ORIGIN:-https://saiyan-ai-virtual-office.rust-sauce.workers.dev}"

python3 "$ROOT/scripts/build_public_office.py"
touch "$DEST/.nojekyll"
# GitHub user-site folders (omamori pattern) keep their own 404.html
# so unknown paths under /saiyan-office/ do not fall through to the store SPA.
cp "$DEST/index.html" "$DEST/404.html"

echo "Built GitHub Pages office at $DEST"
