#!/usr/bin/env python3
"""Yesterday memo uses JST dates only. No invented metrics."""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from yesterday_memo import build_yesterday_memo, yesterday_tokyo  # noqa: E402


def fail(msg: str) -> None:
    raise SystemExit(f"FAIL: {msg}")


def main() -> int:
    now = datetime(2026, 9, 4, 8, 0, tzinfo=timezone.utc)
    yst = yesterday_tokyo(now)
    if yst != "2026-09-03":
        fail(f"yesterday tokyo {yst}")
    status = {
        "queuedInstructions": [
            {
                "assignee_name": "開発担当Bot",
                "room": "海外EC",
                "body": "pages-live",
                "status": "許可待ち",
                "created_at": "2026-09-03T02:36:49.163Z",
            },
            {
                "assignee_name": "開発担当Bot2",
                "room": "AIバーチャルオフィス",
                "body": "old-test",
                "status": "許可待ち",
                "created_at": "2026-09-02T12:32:01.541Z",
            },
        ],
        "cursorAgents": [
            {"name": "Fix LP badges", "status": "できたまま", "lifecycle": "finished"},
        ],
        "grokRooms": [{"name": "司令塔", "status": "動いている", "assignee": "メインAI社員"}],
    }
    memo = build_yesterday_memo(status, now=now)
    if not memo.get("success") or "pages-live" not in memo.get("memo", ""):
        fail(f"expected dated progress line {memo}")
    if "old-test" in memo.get("memo", ""):
        fail("must not include the day-before-yesterday row")
    if "Fix LP badges" in memo.get("memo", ""):
        fail("must not invent yesterday for undated cursorAgents")
    empty = build_yesterday_memo({"queuedInstructions": [], "cursorAgents": [], "grokRooms": []}, now=now)
    if empty.get("success"):
        fail(f"empty status should not succeed {empty}")
    msg = empty.get("msg") or ""
    if "2026-09-03" not in msg or "workers.dev/status" not in msg:
        fail(f"empty diagnostic missing date/source {empty}")
    if msg.strip() == "昨日の日記はまだない":
        fail("bare placeholder leaked")
    html = (ROOT / "frontend" / "index.html").read_text(encoding="utf-8")
    if "YESTERDAY_MEMO_20260904" not in html or "buildYesterdayMemoFromStatus" not in html:
        fail("frontend missing Pages diary builder")
    if 'id="memo-placeholder">昨日の日記はまだない' in html:
        fail("frontend still ships bare empty diary")
    worker = (ROOT / "public-host" / "worker.js").read_text(encoding="utf-8")
    if "function buildYesterdayMemo" not in worker or "handleYesterdayMemo" not in worker:
        fail("worker missing yesterday-memo builder")
    print("PASS yesterday memo JST builder")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
