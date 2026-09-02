#!/usr/bin/env python3
"""Unit checks for local Grok/Cursor office board (no network)."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from office_board import (  # noqa: E402
    CURSOR_AGENTS_HOME,
    ETA_LABEL,
    GROK_ROOM_NAMES,
    LIVE_CURSOR_NAMES,
    ROOM_ASSIGNEES,
    STATUS_BUCKETS,
    TEAMMATE_NAMES,
    cursor_open_url,
    ensure_office_board,
    eta_display,
    instruction_is_delivered,
    normalize_bucket,
    patch_cursor_agent,
    patch_room,
    public_board,
    queue_instruction,
    sanitize_public_detail,
)


def fail(msg: str) -> None:
    raise SystemExit(f"FAIL: {msg}")


def main() -> int:
    os.environ["STAR_OFFICE_OUTBOX"] = str(ROOT / "outbox" / "test-instructions.jsonl")
    os.environ["STAR_OFFICE_DELIVERED"] = str(ROOT / "outbox" / "test-delivered.jsonl")
    Path(os.environ["STAR_OFFICE_DELIVERED"]).write_text("", encoding="utf-8")
    assert STATUS_BUCKETS == ("動いている", "許可待ち", "できたまま")
    assert GROK_ROOM_NAMES == (
        "司令塔",
        "AIバーチャルオフィス",
        "広告運用",
        "海外EC",
        "新規事業会議",
        "Xマーケティング自動化",
        "動画生成",
        "コンサル管理",
        "新規顧客開拓",
    )
    assert ROOM_ASSIGNEES["AIバーチャルオフィス"] == "開発担当Bot2"
    assert ROOM_ASSIGNEES["海外EC"] == "開発担当Bot"
    assert "開発担当Bot2" in TEAMMATE_NAMES
    assert "コンテンツ生成社員" in TEAMMATE_NAMES
    assert len(TEAMMATE_NAMES) == 13

    assert normalize_bucket("running") == "動いている"
    assert normalize_bucket("finished") == "できたまま"
    assert normalize_bucket("pending") == "許可待ち"

    empty = {}
    assert ensure_office_board(empty) is True
    names = [r["name"] for r in empty["grokRooms"]]
    if names != list(GROK_ROOM_NAMES):
        fail(f"rooms {names}")
    if empty["grokRooms"][0]["assignee"] != "メインAI社員":
        fail("司令塔 assignee")
    live_names = [a["name"] for a in empty["cursorAgents"]]
    if live_names != list(LIVE_CURSOR_NAMES):
        fail(f"live cursor jobs {live_names}")
    if any(a.get("sample") for a in empty["cursorAgents"]):
        fail("must not seed sample cursor jobs")
    if "オフィス実況化" in live_names:
        fail("invented replacements must not be seeded")

    assert eta_display({}) == ""
    assert eta_display({"eta": "30分"}) == ""
    assert eta_display({ETA_LABEL: "あと少し"}) == f"{ETA_LABEL} あと少し"

    agent = next(a for a in empty["cursorAgents"] if a["name"].startswith("Grok rooms"))
    assert cursor_open_url(agent) == "https://cursor.com/agents/bc-3356893b-3dfd-4261-92d1-fd6004956913"
    lp = next(a for a in empty["cursorAgents"] if a["name"].startswith("Fix LP badges"))
    assert cursor_open_url(lp) == "https://github.com/rezent011-sketch/skillengine-line-tokuten-lp/pull/3"
    assert cursor_open_url({}) == CURSOR_AGENTS_HOME

    leftover = {"cursorAgents": [{"name": "サンプル: 表示確認", "sample": True, "status": "動いている"}]}
    ensure_office_board(leftover)
    leftover_names = [a["name"] for a in leftover.get("cursorAgents") or []]
    if "サンプル: 表示確認" in leftover_names or "オフィス実況化" in leftover_names:
        fail("sample/invented rows must be stripped")
    if leftover_names != list(LIVE_CURSOR_NAMES):
        fail(f"must replace leftovers with real jobs, got {leftover_names}")

    board = public_board(empty)
    assert board["liveCursorApi"] is False
    assert board["dataSource"] == "local"
    assert [a["name"] for a in board["cursorAgents"]] == list(LIVE_CURSOR_NAMES)
    assert "ライブAPI未接続" not in board["liveApiNote"]
    assert sanitize_public_detail("修行中...") == "待機中"
    assert sanitize_public_detail("待命") == "待機中"

    queued = queue_instruction(empty, {"room": "AIバーチャルオフィス", "text": "状況をまとめて"})
    assert queued and queued["executed"] is False and queued["assignee_name"] == "開発担当Bot2"
    outbox = Path(os.environ["STAR_OFFICE_OUTBOX"])
    if not outbox.is_file():
        fail("instruction send must write outbox/instructions.jsonl")
    last = outbox.read_text(encoding="utf-8").strip().splitlines()[-1]
    row = json.loads(last)
    for key in ("room", "assignee_name", "body", "timestamp"):
        if key not in row or not str(row[key]).strip():
            fail(f"outbox row missing {key}: {last}")
    if row["room"] != "AIバーチャルオフィス" or row["assignee_name"] != "開発担当Bot2" or row["body"] != "状況をまとめて":
        fail(f"outbox fields wrong: {last}")
    board = public_board(empty)
    if not any(q.get("id") == queued["id"] for q in board.get("queuedInstructions") or []):
        fail("queuedInstructions missing from public_board /status payload")
    outbox_before = outbox.read_text(encoding="utf-8")
    delivered_path = Path(os.environ["STAR_OFFICE_DELIVERED"])
    delivered_path.write_text(
        json.dumps(
            {
                "room": "AIバーチャルオフィス",
                "assignee_name": "開発担当Bot2",
                "body": "状況をまとめて",
                "timestamp": queued["timestamp"],
                "delivered": True,
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    flipped = public_board(empty)
    match = next((q for q in flipped.get("queuedInstructions") or [] if q.get("id") == queued["id"]), None)
    if not match or not instruction_is_delivered(match) or match.get("status") != "できたまま":
        fail(f"delivered.jsonl must flip queuedInstructions to delivered/できたまま, got {match}")
    if match.get("queued") is not False:
        fail("delivered item must leave the pending queue")
    if outbox.read_text(encoding="utf-8") != outbox_before:
        fail("must not wipe instructions.jsonl when applying delivered.jsonl")
    still_new = queue_instruction(empty, {"room": "司令塔", "text": "キュー確認"})
    if not still_new or still_new.get("status") != "許可待ち":
        fail("new Safari instructions must still queue")
    last2 = outbox.read_text(encoding="utf-8").strip().splitlines()[-1]
    row2 = json.loads(last2)
    if row2.get("body") != "キュー確認" or row2.get("room") != "司令塔":
        fail(f"new instruction must append instructions.jsonl: {last2}")
    if outbox_before not in outbox.read_text(encoding="utf-8"):
        fail("existing outbox lines must remain until copied to delivered.jsonl")
    delivered_path.write_text(
        delivered_path.read_text(encoding="utf-8")
        + json.dumps({"room": "司令塔", "body": "キュー確認", "delivered": True}, ensure_ascii=False)
        + "\n",
        encoding="utf-8",
    )
    after_q = public_board(empty)
    qmatch = next((q for q in after_q.get("queuedInstructions") or [] if q.get("id") == still_new["id"]), None)
    if not qmatch or qmatch.get("status") != "できたまま" or qmatch.get("queued") is not False:
        fail(f"キュー確認 must leave 許可待ち after delivered.jsonl, got {qmatch}")

    html = (ROOT / "frontend" / "index.html").read_text(encoding="utf-8")
    for token in (
        "待命",
        "暂无访客",
        "暂无昨日日记",
        "zh-CN",
        "lang-btn-cn",
        "修行中",
        "Star 的像素办公室",
        "访客动画",
        "办公桌（旧）",
        "办公桌",
        "I18N.zh",
        "nameMap.zh",
        "nameMap['zh']",
        "工作中",
        "officeSample: 'サンプル'",
    ):
        if token in html:
            fail(f"frontend/index.html still contains {token!r}")
    if "officeDelivered: '指示（配送済み）'" not in html:
        fail("delivered instruction label missing")
    if html.count("サンプル") != 1 or "sampleMarkers = ['サンプル'" not in html:
        fail("サンプル may exist only as a hide-filter, never as a visible label")
    if "const uiLang = 'ja'" not in html or 'lang="ja"' not in html:
        fail("UI language must be forced to ja")
    if "昨日の日記はまだない" not in html or "訪問者はいない" not in html or "待機中" not in html:
        fail("Japanese empty states missing from index.html")
    shim = (ROOT / "scripts" / "public_office_shim.js").read_text(encoding="utf-8")
    if "「' + assignee + '」に渡しました（未実行）" not in shim or "開発担当Bot2" not in shim:
        fail("public office shim must queue instructions to room assignees")
    sys.path.insert(0, str(ROOT / "scripts"))
    from build_public_office import sanitize_public_html  # noqa: E402

    public_html = sanitize_public_html(html)
    if "司令塔" not in public_html or "動いている" not in public_html or "AIバーチャルオフィス" not in public_html:
        fail("public HTML lost the live office board")
    for token in ("ロブスター", "Gemini APIキー", "GEMINI APIキー", "GEMINI_API_KEY"):
        if token in public_html:
            fail(f"public HTML still ships {token!r}")
    build = (ROOT / "scripts" / "build_public_office.py").read_text(encoding="utf-8")
    if "saiyan-ai-virtual-office.surge.sh" not in build:
        fail("public office must publish to a named surge.sh domain")

    print("OK office_board")
    return 0


if __name__ == "__main__":
    sys.exit(main())
