#!/usr/bin/env python3
"""Public office /set_state queue (no network)."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
os.environ["PUBLIC_OFFICE_QUEUE"] = str(ROOT / "outbox" / "test-public-queue.json")
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "public-host"))

from app import app, queue_path, _save_queue_state  # noqa: E402


def fail(msg: str) -> None:
    raise SystemExit(f"FAIL: {msg}")


def main() -> int:
    queue_path().parent.mkdir(parents=True, exist_ok=True)
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
    sys.path.insert(0, str(ROOT / "scripts"))
    from build_public_office import sanitize_public_html  # noqa: E402

    sample = "await fetch('/set_state', { method: 'POST' })\nreturn fetch('/status', { cache: 'no-store' })"
    rewritten = sanitize_public_html(sample)
    if "fetch('https://saiyan-ai-virtual-office.rust-sauce.workers.dev/set_state'" not in rewritten:
        fail("public HTML rewrite must use rust-sauce workers set_state URL")
    if "fetch('/set_state'" in rewritten or "fetch('/status'" in rewritten:
        fail("public HTML rewrite left relative office fetches")
    print("PASS public office /set_state queue")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
