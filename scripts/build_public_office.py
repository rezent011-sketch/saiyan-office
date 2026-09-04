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

DEST = Path(os.environ.get("PUBLIC_OFFICE_DEST", ROOT / "public-office"))
FRONTEND = ROOT / "frontend"
DOMAIN = "saiyan-ai-virtual-office.surge.sh"
API_ORIGIN = os.environ.get(
    "PUBLIC_OFFICE_API_ORIGIN",
    "https://saiyan-ai-virtual-office.rust-sauce.workers.dev",
).strip().rstrip("/")
ASSET_PREFIX = os.environ.get("PUBLIC_ASSET_PREFIX", "").strip().rstrip("/")
RELATIVE_ASSETS = os.environ.get("PUBLIC_RELATIVE_ASSETS", "").strip().lower() in {"1", "true", "yes"}
WRITE_CNAME = os.environ.get("PUBLIC_WRITE_CNAME", "1").strip().lower() not in {"0", "false", "no"}
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
    html = html.replace("{{VERSION_TIMESTAMP}}", "public-20260903a")
    if "PAGES_PUBLISH_20260903" not in html:
        html = html.replace(
            "<title>AIバーチャルオフィス</title>",
            "<title>AIバーチャルオフィス</title>\n    <!-- PAGES_PUBLISH_20260903 -->",
            1,
        )
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
    if API_ORIGIN:
        html = html.replace("fetch('/set_state'", f"fetch('{API_ORIGIN}/set_state'")
        html = html.replace('fetch("/set_state"', f'fetch("{API_ORIGIN}/set_state"')
        html = html.replace("fetch('/status'", f"fetch('{API_ORIGIN}/status'")
        html = html.replace('fetch("/status"', f'fetch("{API_ORIGIN}/status"')
        html = html.replace("fetch('/status.json'", f"fetch('{API_ORIGIN}/status.json'")
        html = html.replace("fetch('/yesterday-memo'", f"fetch('{API_ORIGIN}/yesterday-memo'")
        html = html.replace('fetch("/yesterday-memo"', f'fetch("{API_ORIGIN}/yesterday-memo"')
    return html


def apply_asset_prefix(html: str) -> str:
    if RELATIVE_ASSETS:
        return html.replace("/static/", "static/")
    if not ASSET_PREFIX:
        return html
    return html.replace("/static/", f"{ASSET_PREFIX}/static/")


def assert_public_html(html: str) -> None:
    if "AIバーチャルオフィス" not in html:
        raise SystemExit("public HTML missing title AIバーチャルオフィス")
    if "司令塔" not in html or "動いている" not in html:
        raise SystemExit("public HTML missing real Grok desk / bucket copy")
    if "デスクへの指示を書く" not in html:
        raise SystemExit("public HTML missing instruction form")
    if 'id="staff-floor"' not in html or "Claude Code開発" not in html or "メインAI社員" not in html:
        raise SystemExit("public HTML missing named staff floor")
    if "STAFF_BIND_FIX_20260902E" not in html:
        raise SystemExit("public HTML missing staff bind fix")
    if "NO_OVERLAY_CARDS_20260903" not in html:
        raise SystemExit("public HTML still paints overlay staff cards")
    if "STAFF_REST_WORK_20260903" not in html or "staffIsOnDuty" not in html:
        raise SystemExit("public HTML missing busy-desk / sofa-rest poses")
    if "WAITING_ROOM_20260904" not in html or "待機部屋" not in html:
        raise SystemExit("public HTML missing the separate waiting room")
    if "display: none !important;" not in html or 'class="staff-desk"' in html:
        raise SystemExit("public HTML must not emit gold staff cards over the office")
    if "{ name: '開発担当Bot', room: '海外EC'" not in html:
        raise SystemExit("public HTML must bind 海外EC to 開発担当Bot")
    if "mate.task || mate.currentTask || room.task" in html:
        raise SystemExit("public HTML still inherits room.task onto every staff card")
    if "コンテンツ生成社員" in html:
        raise SystemExit("public HTML still contains old sample staff")
    worker_set_state = f"{API_ORIGIN}/set_state"
    if worker_set_state not in html or f"fetch('{worker_set_state}'" not in html:
        raise SystemExit("public HTML must fetch set_state from the rust-sauce workers origin")
    if "fetch('/set_state'" in html or 'fetch("/set_state"' in html:
        raise SystemExit("public HTML still fetches relative /set_state")
    if "fetch('/status'" in html or 'fetch("/status"' in html:
        raise SystemExit("public HTML still fetches relative /status")
    if f"{API_ORIGIN}/yesterday-memo" not in html:
        raise SystemExit("public HTML must load yesterday memo from the rust-sauce workers origin")
    if "YESTERDAY_MEMO_20260904" not in html or "buildYesterdayMemoFromStatus" not in html:
        raise SystemExit("public HTML missing Pages yesterday-memo builder")
    if 'id="memo-placeholder">昨日の日記はまだない' in html:
        raise SystemExit("public HTML still ships the bare empty diary placeholder")
    if RELATIVE_ASSETS:
        if 'src="static/' not in html:
            raise SystemExit("public HTML missing relative static/ asset paths")
        if 'src="/static/' in html or "url('/static/" in html:
            raise SystemExit("public HTML still uses root /static/ paths")
    elif ASSET_PREFIX:
        if f"{ASSET_PREFIX}/static/" not in html:
            raise SystemExit("public HTML missing project Pages asset prefix")
        if 'src="/static/' in html or "url('/static/" in html:
            raise SystemExit("public HTML still uses root /static/ paths")
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
        + '<script src="/static/public-office-shim.js?v=public-20260903a"></script>\n    '
    )
    needle = '<script src="/static/vendor/phaser-3.80.1.min.js'
    if needle not in html:
        raise SystemExit("phaser script tag missing")
    html = html.replace(needle, shim_tag + needle, 1)
    html = apply_asset_prefix(html)
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
    sys.path.insert(0, str(ROOT / "scripts"))
    from yesterday_memo import STATUS_URL as MEMO_STATUS_URL  # noqa: E402
    from yesterday_memo import build_yesterday_memo  # noqa: E402

    memo_status = dict(status)
    try:
        import urllib.request

        req = urllib.request.Request(MEMO_STATUS_URL, headers={"User-Agent": "saiyan-office-pages"})
        with urllib.request.urlopen(req, timeout=12) as res:
            live = json.loads(res.read().decode("utf-8"))
        if isinstance(live, dict):
            memo_status = live
    except Exception:
        pass
    memo = build_yesterday_memo(memo_status)
    (DEST / "yesterday-memo.json").write_text(
        json.dumps(memo, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (DEST / ".nojekyll").write_text("", encoding="utf-8")
    if WRITE_CNAME:
        (DEST / "CNAME").write_text(DOMAIN + "\n", encoding="utf-8")
    host = f"https://rezent011-sketch.github.io{ASSET_PREFIX}/" if ASSET_PREFIX else f"https://{DOMAIN}"
    print(f"Built {DEST} for {host}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
