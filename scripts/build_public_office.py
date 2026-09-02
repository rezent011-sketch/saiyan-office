#!/usr/bin/env python3
"""Build a Flask-free pixel office for a named surge.sh host."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from office_board import public_board  # noqa: E402

DEST = ROOT / "public-office"
FRONTEND = ROOT / "frontend"
DOMAIN = "saiyan-ai-virtual-office.surge.sh"
SKIP_NAMES = {
    "electron-standalone.html",
    "join.html",
    "invite.html",
    "join-office-skill.md",
    "office-agent-push.py",
}


def main() -> int:
    if DEST.exists():
        shutil.rmtree(DEST)
    static_dir = DEST / "static"
    static_dir.mkdir(parents=True)

    for src in FRONTEND.rglob("*"):
        if not src.is_file():
            continue
        rel = src.relative_to(FRONTEND)
        if rel.parts and rel.parts[0] in SKIP_NAMES:
            continue
        if src.name in SKIP_NAMES:
            continue
        dest = static_dir / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)

    html = (FRONTEND / "index.html").read_text(encoding="utf-8")
    html = html.replace("{{VERSION_TIMESTAMP}}", "public-20260902")
    shim_tag = '<script src="/static/public-office-shim.js?v=public-20260902"></script>\n    '
    needle = '<script src="/static/vendor/phaser-3.80.1.min.js'
    if needle not in html:
        raise SystemExit("phaser script tag missing")
    html = html.replace(needle, shim_tag + needle, 1)
    (DEST / "index.html").write_text(html, encoding="utf-8")
    shutil.copy2(ROOT / "scripts" / "public_office_shim.js", static_dir / "public-office-shim.js")

    board = public_board({})
    status = {
        "state": "idle",
        "detail": "待機中",
        "progress": 0,
        "officeName": "AIバーチャルオフィス",
        **board,
    }
    (DEST / "status.json").write_text(
        json.dumps(status, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (DEST / "CNAME").write_text(DOMAIN + "\n", encoding="utf-8")
    print(f"Built {DEST} for https://{DOMAIN}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
