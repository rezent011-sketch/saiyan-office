#!/usr/bin/env bash
# Build the current public office for GitHub Pages project URL
# https://rezent011-sketch.github.io/saiyan-office/
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEST="${1:-"$ROOT/_site"}"

export PUBLIC_OFFICE_DEST="$DEST"
export PUBLIC_ASSET_PREFIX="/saiyan-office"
export PUBLIC_WRITE_CNAME=0
export PUBLIC_OFFICE_API_ORIGIN="${PUBLIC_OFFICE_API_ORIGIN:-https://saiyan-ai-virtual-office.rust-sauce.workers.dev}"

python3 "$ROOT/scripts/build_public_office.py"
touch "$DEST/.nojekyll"

echo "Built GitHub Pages office at $DEST"
