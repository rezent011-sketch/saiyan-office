#!/usr/bin/env python3
"""Unit checks for local Grok/Cursor office board (no network)."""

from __future__ import annotations

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
    STATUS_BUCKETS,
    TEAMMATE_NAMES,
    cursor_open_url,
    ensure_office_board,
    eta_display,
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
    assert STATUS_BUCKETS == ("動いている", "許可待ち", "できたまま")
    assert GROK_ROOM_NAMES == (
        "司令塔",
        "Xマーケティング自動化",
        "動画生成",
        "広告運用",
        "AIバーチャルオフィス",
    )
    assert "新規顧客開拓Bot" in TEAMMATE_NAMES
    assert len(TEAMMATE_NAMES) == 12

    assert normalize_bucket("running") == "動いている"
    assert normalize_bucket("finished") == "できたまま"
    assert normalize_bucket("pending") == "許可待ち"
    assert normalize_bucket("許可待ち") == "許可待ち"

    empty = {}
    assert ensure_office_board(empty) is True
    names = [r["name"] for r in empty["grokRooms"]]
    if names != list(GROK_ROOM_NAMES):
        fail(f"rooms {names}")
    if any(r.get("url") for r in empty["grokRooms"]):
        fail("default room URLs must stay empty (do not invent)")
    live_names = [a["name"] for a in empty["cursorAgents"]]
    if live_names != list(LIVE_CURSOR_NAMES):
        fail(f"live cursor jobs {live_names}")
    if any(a.get("sample") for a in empty["cursorAgents"]):
        fail("must not seed sample cursor jobs")

    assert eta_display({}) == ""
    assert eta_display({"eta": "30分"}) == ""
    assert eta_display({ETA_LABEL: ""}) == ""
    assert eta_display({ETA_LABEL: "あと少し"}) == f"{ETA_LABEL} あと少し"
    assert eta_display({"eta": f"{ETA_LABEL} 記載あり"}) == f"{ETA_LABEL} 記載あり"

    assert cursor_open_url({}) == CURSOR_AGENTS_HOME
    assert cursor_open_url({"url": "https://example.com/nope"}) == CURSOR_AGENTS_HOME
    assert cursor_open_url({"url": "https://cursor.com/agents/bc-demo"}) == "https://cursor.com/agents/bc-demo"

    state = {}
    ensure_office_board(state)
    assert patch_room(state, {"name": "広告運用", "status": "動いている"})
    assert next(r for r in state["grokRooms"] if r["name"] == "広告運用")["status"] == "動いている"
    assert not patch_room(state, {"name": "架空ルーム", "status": "動いている"})

    leftover = {"cursorAgents": [{"name": "サンプル: 表示確認", "sample": True, "status": "動いている", "lifecycle": "running"}]}
    ensure_office_board(leftover)
    leftover_names = [a["name"] for a in leftover.get("cursorAgents") or []]
    if "サンプル: 表示確認" in leftover_names:
        fail("sample cursor rows must be stripped")
    if leftover_names != list(LIVE_CURSOR_NAMES):
        fail(f"samples must be replaced by live jobs, got {leftover_names}")

    board = public_board(state)
    assert board["liveCursorApi"] is False
    assert [a["name"] for a in board["cursorAgents"]] == list(LIVE_CURSOR_NAMES)
    assert "ライブAPI未接続" not in board["liveApiNote"]
    assert sanitize_public_detail("修行中...") == "待機中"
    assert sanitize_public_detail("待命") == "待機中"
    assert sanitize_public_detail("暫無昨日日記") == "待機中"
    assert board["buckets"] == list(STATUS_BUCKETS)
    assert queue_instruction(state, {"room": "架空", "text": "no"}) is None
    queued = queue_instruction(state, {"room": "司令塔", "text": "状況をまとめて"})
    assert queued and queued["executed"] is False and queued["status"] == "許可待ち"
    assert any(q["text"] == "状況をまとめて" for q in public_board(state)["queuedInstructions"])
    outbox = Path(os.environ.get("STAR_OFFICE_OUTBOX", str(ROOT / "outbox" / "instructions.jsonl")))
    if not outbox.is_file():
        fail("instruction send must write outbox/instructions.jsonl")
    last = outbox.read_text(encoding="utf-8").strip().splitlines()[-1]
    if "状況をまとめて" not in last or "司令塔" not in last:
        fail(f"outbox row missing room/text: {last}")
    print("OK office_board")
    return 0


if __name__ == "__main__":
    sys.exit(main())
