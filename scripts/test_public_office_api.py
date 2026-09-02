#!/usr/bin/env python3
"""Public office /set_state queue (no network)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "public-host"))

from app import QUEUE_PATH, app, _save_queue_state  # noqa: E402


def fail(msg: str) -> None:
    raise SystemExit(f"FAIL: {msg}")


def main() -> int:
    QUEUE_PATH.parent.mkdir(parents=True, exist_ok=True)
    _save_queue_state({"queuedInstructions": []})
    client = app.test_client()

    res = client.post(
        "/set_state",
        data=json.dumps({"instruction": {"room": "AIバーチャルオフィス", "body": "test"}}),
        content_type="application/json",
    )
    if res.status_code != 200:
        fail(f"POST /set_state {res.status_code} {res.data}")
    payload = res.get_json()
    if payload.get("status") != "ok":
        fail(f"ack status {payload}")
    if "開発担当Bot2" not in str(payload.get("msg") or "") or "未実行" not in str(payload.get("msg") or ""):
        fail(f"ack msg {payload}")
    queued = payload.get("queuedInstruction") or {}
    if queued.get("room") != "AIバーチャルオフィス" or queued.get("assignee_name") != "開発担当Bot2":
        fail(f"queuedInstruction {queued}")
    if queued.get("body") != "test" or not queued.get("timestamp"):
        fail(f"queued fields {queued}")

    status = client.get("/status").get_json()
    rows = status.get("queuedInstructions") or []
    if not any(isinstance(r, dict) and r.get("body") == "test" and r.get("assignee_name") == "開発担当Bot2" for r in rows):
        fail(f"GET /status missing queued row {rows}")
    if "AIバーチャルオフィス" not in {r.get("name") for r in status.get("grokRooms") or []}:
        fail("GET /status missing real rooms")
    if status.get("buckets") != ["動いている", "許可待ち", "できたまま"]:
        fail(f"buckets {status.get('buckets')}")

    outbox = client.get("/outbox.json").get_json()
    if not any(isinstance(r, dict) and r.get("body") == "test" for r in outbox.get("queuedInstructions") or []):
        fail(f"GET /outbox.json {outbox}")
    print("PASS public office /set_state queue")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
