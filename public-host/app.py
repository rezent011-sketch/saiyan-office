#!/usr/bin/env python3
"""Public HTTPS office origin: pixel board + Flask /set_state queue. No posts/ads/billing."""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "scripts"))

from office_board import public_board, queue_instruction  # noqa: E402

QUEUE_PATH = Path(os.environ.get("PUBLIC_OFFICE_QUEUE", str(ROOT / "public-queue" / "queue.json")))
PUBLIC_DIR = Path(os.environ.get("PUBLIC_OFFICE_DIR", str(ROOT / "public-office")))
SURGE_ORIGIN = os.environ.get("PUBLIC_OFFICE_SURGE", "https://saiyan-ai-virtual-office.surge.sh")

app = Flask(__name__)


def _load_queue_state() -> dict:
    state: dict = {"queuedInstructions": []}
    if QUEUE_PATH.is_file():
        try:
            data = json.loads(QUEUE_PATH.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                state = data
            elif isinstance(data, list):
                state = {"queuedInstructions": data}
        except Exception:
            state = {"queuedInstructions": []}
    if not isinstance(state.get("queuedInstructions"), list):
        state["queuedInstructions"] = []
    return state


def _save_queue_state(state: dict) -> None:
    QUEUE_PATH.parent.mkdir(parents=True, exist_ok=True)
    rows = state.get("queuedInstructions") or []
    if not isinstance(rows, list):
        rows = []
    payload = {
        "queuedInstructions": rows[-80:],
        "updated_at": datetime.now().isoformat(),
    }
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    QUEUE_PATH.write_text(text, encoding="utf-8")
    token = (os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or "").strip()
    if not token:
        return
    import base64
    import urllib.request

    repo = os.environ.get("GITHUB_REPO", "rezent011-sketch/saiyan-office")
    path = os.environ.get("GITHUB_QUEUE_PATH", "public-queue/queue.json")
    branch = os.environ.get("GITHUB_BRANCH", "cursor/grok-cursor-office-board-6913")
    api = f"https://api.github.com/repos/{repo}/contents/{path}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "saiyan-office-public-queue",
    }
    sha = None
    try:
        req = urllib.request.Request(api + "?ref=" + branch, headers=headers, method="GET")
        with urllib.request.urlopen(req, timeout=8) as resp:
            sha = json.loads(resp.read().decode("utf-8")).get("sha")
    except Exception:
        sha = None
    body = {
        "message": "queue: desk instruction",
        "content": base64.b64encode(text.encode("utf-8")).decode("ascii"),
        "branch": branch,
    }
    if sha:
        body["sha"] = sha
    try:
        req = urllib.request.Request(
            api,
            data=json.dumps(body).encode("utf-8"),
            headers={**headers, "Content-Type": "application/json"},
            method="PUT",
        )
        urllib.request.urlopen(req, timeout=8).read()
    except Exception:
        pass


def _cors(resp):
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    resp.headers["Cache-Control"] = "no-store"
    return resp


@app.after_request
def add_cors(resp):
    return _cors(resp)


@app.route("/set_state", methods=["POST", "OPTIONS"])
def set_state():
    if request.method == "OPTIONS":
        return _cors(app.make_response(("", 204)))
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"status": "error", "msg": "invalid json"}), 400
    if not isinstance(data.get("instruction"), dict):
        return jsonify({"status": "ok"})
    state = _load_queue_state()
    queued = queue_instruction(state, data["instruction"])
    if queued is None:
        return jsonify({"status": "error", "msg": "指示を書けませんでした（部屋と本文が必要です）"}), 400
    _save_queue_state(state)
    return jsonify({
        "status": "ok",
        "msg": f"「{queued['assignee_name']}」に渡しました（未実行）",
        "queuedInstruction": {
            "room": queued["room"],
            "assignee_name": queued["assignee_name"],
            "body": queued["body"],
            "timestamp": queued["timestamp"],
        },
    })


@app.route("/status", methods=["GET"])
@app.route("/status.json", methods=["GET"])
def status():
    state = _load_queue_state()
    board = public_board(state)
    return jsonify({
        "state": "idle",
        "detail": "待機中",
        "progress": 0,
        "officeName": "AIバーチャルオフィス",
        **board,
    })


@app.route("/outbox.json", methods=["GET"])
@app.route("/outbox", methods=["GET"])
def outbox():
    return jsonify({"queuedInstructions": _load_queue_state().get("queuedInstructions") or []})


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"ok": True})


@app.route("/yesterday-memo", methods=["GET"])
def yesterday_memo():
    return jsonify({"success": False, "msg": "昨日の日記はまだない"})


@app.route("/agents", methods=["GET"])
def agents():
    return jsonify([])


@app.route("/", methods=["GET"])
def index():
    index_html = PUBLIC_DIR / "index.html"
    if index_html.is_file():
        return send_from_directory(PUBLIC_DIR, "index.html")
    frontend = ROOT / "frontend" / "index.html"
    if frontend.is_file():
        return send_from_directory(frontend.parent, "index.html")
    return jsonify({"ok": False, "msg": "office html missing"}), 404


@app.route("/<path:path>", methods=["GET"])
def public_files(path: str):
    candidate = PUBLIC_DIR / path
    if candidate.is_file():
        return send_from_directory(PUBLIC_DIR, path)
    static_candidate = PUBLIC_DIR / "static" / path
    if path.startswith("static/") and (PUBLIC_DIR / path).is_file():
        return send_from_directory(PUBLIC_DIR, path)
    frontend = ROOT / "frontend" / path
    if frontend.is_file():
        return send_from_directory(frontend.parent, path)
    return jsonify({"ok": False, "msg": "not found", "surge": SURGE_ORIGIN}), 404


def main() -> int:
    from build_public_office import main as build_public  # noqa: E402

    if not (PUBLIC_DIR / "index.html").is_file():
        build_public()
    QUEUE_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not QUEUE_PATH.is_file():
        _save_queue_state({"queuedInstructions": []})
    host = os.environ.get("PUBLIC_OFFICE_HOST", "0.0.0.0")
    port = int(os.environ.get("PORT") or os.environ.get("PUBLIC_OFFICE_PORT") or "8080")
    app.run(host=host, port=port, debug=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
