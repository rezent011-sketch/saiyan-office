#!/usr/bin/env python3
"""Unit checks for local Grok/Cursor office board (no network)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from office_board import (  # noqa: E402
    CURSOR_AGENTS_HOME,
    ETA_LABEL,
    GROK_ROOM_NAMES,
    STATUS_BUCKETS,
    TEAMMATE_NAMES,
    cursor_open_url,
    ensure_office_board,
    eta_display,
    normalize_bucket,
    patch_cursor_agent,
    patch_room,
    public_board,
)


def fail(msg: str) -> None:
    raise SystemExit(f"FAIL: {msg}")


def main() -> int:
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
    if not all(a.get("sample") for a in empty["cursorAgents"]):
        fail("default cursor rows must be marked sample")
    if any(a.get("url") not in ("", CURSOR_AGENTS_HOME) for a in empty["cursorAgents"]):
        fail("default cursor URLs must be cursor.com/agents or empty")

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

    assert patch_cursor_agent(state, {"name": "サンプル: 表示確認", "lifecycle": "finished"})
    row = next(a for a in state["cursorAgents"] if a["name"] == "サンプル: 表示確認")
    assert row["status"] == "できたまま"
    assert row["lifecycle"] == "finished"

    board = public_board(state)
    assert board["liveCursorApi"] is False
    assert board["buckets"] == list(STATUS_BUCKETS)
    print("OK office_board")
    return 0


if __name__ == "__main__":
    sys.exit(main())
