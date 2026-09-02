#!/usr/bin/env python3
"""Star Office UI smoke test (non-destructive).

Usage:
  python3 scripts/smoke_test.py --base-url http://127.0.0.1:19000

Optional env:
  SMOKE_AUTH_BEARER=xxxx   # if your gateway/proxy requires bearer auth
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request


REQUIRED_ENDPOINTS = [
    ("GET", "/", 200),
    ("GET", "/health", 200),
    ("GET", "/status", 200),
    ("GET", "/agents", 200),
    ("GET", "/yesterday-memo", 200),
]


def req(method: str, url: str, body: dict | None = None, token: str = "") -> tuple[int, str]:
    data = None
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"

    r = urllib.request.Request(url=url, method=method, data=data, headers=headers)
    try:
        with urllib.request.urlopen(r, timeout=8) as resp:
            raw = resp.read().decode("utf-8", errors="ignore")
            return resp.status, raw
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="ignore") if hasattr(e, "read") else str(e)
        return e.code, raw
    except Exception as e:
        return 0, str(e)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default="http://127.0.0.1:19000", help="Base URL of Star Office UI service")
    args = ap.parse_args()

    base = args.base_url.rstrip("/")
    token = os.getenv("SMOKE_AUTH_BEARER", "").strip()

    failures: list[str] = []
    print(f"[smoke] base={base}")

    for method, path, expected in REQUIRED_ENDPOINTS:
        code, body = req(method, base + path, token=token)
        if code != expected:
            failures.append(f"{method} {path}: expected {expected}, got {code}, body={body[:200]}")
        else:
            print(f"  OK  {method} {path} -> {code}")

    # non-destructive state update probe
    code, body = req("POST", base + "/set_state", {"state": "idle", "detail": "smoke-check"}, token=token)
    if code != 200:
        failures.append(f"POST /set_state failed: {code}, body={body[:200]}")
    else:
        print("  OK  POST /set_state -> 200")

    code, body = req("GET", base + "/status", token=token)
    try:
        status = json.loads(body) if code == 200 else {}
    except Exception:
        status = {}
    rooms = status.get("grokRooms") if isinstance(status, dict) else None
    agents = status.get("cursorAgents") if isinstance(status, dict) else None
    buckets = status.get("buckets") if isinstance(status, dict) else None
    expected_rooms = {"司令塔", "Xマーケティング自動化", "動画生成", "広告運用", "AIバーチャルオフィス"}
    expected_buckets = ["動いている", "許可待ち", "できたまま"]
    if not isinstance(rooms, list) or {r.get("name") for r in rooms if isinstance(r, dict)} != expected_rooms:
        failures.append(f"GET /status missing canonical grokRooms, got={rooms}")
    else:
        print("  OK  /status grokRooms")
    if buckets != expected_buckets:
        failures.append(f"GET /status buckets mismatch, got={buckets}")
    else:
        print("  OK  /status buckets")
    if not isinstance(agents, list) or not any(a.get("sample") for a in agents if isinstance(a, dict)):
        failures.append("GET /status cursorAgents should include sample rows")
    else:
        invented = [a for a in agents if isinstance(a, dict) and str(a.get("url") or "") and not str(a.get("url")).startswith("https://cursor.com/agents")]
        if invented:
            failures.append(f"cursorAgents has non-cursor.com URL: {invented}")
        else:
            print("  OK  /status cursorAgents (sample, no invented URLs)")
    if status.get("liveCursorApi"):
        failures.append("liveCursorApi must be false (local JSON only)")
    else:
        print("  OK  liveCursorApi is false")

    if failures:
        print("\n[smoke] FAIL")
        for f in failures:
            print(" -", f)
        return 1

    print("\n[smoke] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
