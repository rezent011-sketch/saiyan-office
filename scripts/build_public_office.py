#!/usr/bin/env python3
"""Build a Flask-free pixel office for a named surge.sh host."""

from __future__ import annotations

import json
import os
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from office_board import public_board  # noqa: E402

DEST = ROOT / "public-office"
FRONTEND = ROOT / "frontend"
DOMAIN = "saiyan-ai-virtual-office.surge.sh"
API_ORIGIN = os.environ.get(
    "PUBLIC_OFFICE_API_ORIGIN",
    "https://saiyan-ai-virtual-office.rust-sauce.workers.dev",
).strip().rstrip("/")
SKIP_NAMES = {
    "electron-standalone.html",
    "join.html",
    "invite.html",
    "join-office-skill.md",
    "office-agent-push.py",
}
PUBLIC_BANNED = ("ロブスター", "Gemini APIキー", "GEMINI APIキー", "GEMINI_API_KEY")


def _strip_id_block(html: str, element_id: str) -> str:
    pattern = rf'<([a-zA-Z0-9]+)([^>]*\bid="{re.escape(element_id)}"[^>]*)>.*?</\1>'
    return re.sub(pattern, "", html, count=1, flags=re.S)


def sanitize_public_html(html: str) -> str:
    """Keep the pixel board; drop broker/Gemini/drawer copy from the public page."""
    html = html.replace("{{VERSION_TIMESTAMP}}", "public-20260902")
    for element_id in (
        "asset-drawer-backdrop",
        "asset-drawer",
        "btn-open-drawer",
        "asset-broker-panel",
        "asset-gemini-panel",
        "gemini-api-key-input",
        "gemini-api-doc-link",
    ):
        html = _strip_id_block(html, element_id)
    html = re.sub(r'<button id="btn-open-drawer"[^>]*>.*?</button>', "", html, flags=re.S)
    replacements = {
        "ロブスターにはどんな家をおすすめしますか": "",
        "What kind of house would you recommend for Lobster?": "",
        "Haixin Lobster Office": "AIバーチャルオフィス",
        "任意：画像生成APIキーを設定（未設定でも基本機能は利用可）": "",
        "❌ 生成失敗：GEMINI APIキーが未設定です。下で入力して保存してください。": "",
        "GEMINI_API_KEY を貼り付け（入力は非表示）": "",
        "📘 Google API Keyの取得方法": "",
        "🔐 API設定（折りたたみ）": "",
        "🦞": "",
    }
    for old, new in replacements.items():
        html = html.replace(old, new)
    html = re.sub(r"Gemini APIキー", "", html, flags=re.I)
    html = re.sub(r"GEMINI APIキー", "", html)
    html = html.replace("GEMINI_API_KEY", "")
    html = html.replace("ロブスター", "")
    return html


def assert_public_html(html: str) -> None:
    if "AIバーチャルオフィス" not in html:
        raise SystemExit("public HTML missing title AIバーチャルオフィス")
    if "司令塔" not in html or "動いている" not in html:
        raise SystemExit("public HTML missing real Grok desk / bucket copy")
    if "デスクへの指示を書く" not in html:
        raise SystemExit("public HTML missing instruction form")
    for token in PUBLIC_BANNED + ("待命", "暂无访客", "zh-CN"):
        if token in html:
            raise SystemExit(f"public HTML still contains {token!r}")


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

    html = sanitize_public_html((FRONTEND / "index.html").read_text(encoding="utf-8"))
    api_origin_js = (
        f'<script>self.__PUBLIC_OFFICE_API_ORIGIN={json.dumps(API_ORIGIN)};</script>\n    '
        if API_ORIGIN
        else ""
    )
    shim_tag = (
        api_origin_js
        + '<script src="/static/public-office-shim.js?v=public-20260902"></script>\n    '
    )
    needle = '<script src="/static/vendor/phaser-3.80.1.min.js'
    if needle not in html:
        raise SystemExit("phaser script tag missing")
    html = html.replace(needle, shim_tag + needle, 1)
    assert_public_html(html)
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
