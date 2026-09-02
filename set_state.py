#!/usr/bin/env python3
"""Saiyan Officeの状態を更新するスクリプト（テストおよびエージェント連携用）。

ローカルの state.json を読み書きします。Grok部屋 / Cursor Cloud Agent の表示も
このファイル経由です。ライブの有料APIには接続しません。

  python3 set_state.py idle
  python3 set_state.py executing "パイプライン実行中..."
  python3 set_state.py room 司令塔 動いている
  python3 set_state.py room 広告運用 許可待ち
  python3 set_state.py teammate メインAI社員 動いている
  python3 set_state.py cursor "オフィス実況化" running
  python3 set_state.py cursor "LP空き直し" finished
"""

import json
import os
import sys
from datetime import datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ROOT, "backend"))

from office_board import (  # noqa: E402
    CURSOR_AGENTS_HOME,
    GROK_ROOM_NAMES,
    STATUS_BUCKETS,
    TEAMMATE_NAMES,
    ensure_office_board,
    normalize_bucket,
    normalize_lifecycle,
    patch_cursor_agent,
    patch_room,
    patch_teammate,
    queue_instruction,
)

STATE_FILE = os.environ.get(
    "STAR_OFFICE_STATE_FILE",
    os.path.join(ROOT, "state.json"),
)

VALID_STATES = [
    "idle",
    "writing",
    "receiving",
    "replying",
    "researching",
    "executing",
    "syncing",
    "error",
]


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            state = json.load(f)
    else:
        state = {
            "state": "idle",
            "detail": "待機中",
            "progress": 0,
            "officeName": "Saiyan Office 🐉",
            "updated_at": datetime.now().isoformat(),
        }
    if not isinstance(state, dict):
        state = {}
    ensure_office_board(state)
    return state


def save_state(state):
    state["updated_at"] = datetime.now().isoformat()
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def usage() -> None:
    print("使用法:")
    print("  python set_state.py <state> [detail]")
    print(f"    状態: {', '.join(VALID_STATES)}")
    print("  python set_state.py room <部屋名> <動いている|許可待ち|できたまま> [url]")
    print(f"    部屋: {', '.join(GROK_ROOM_NAMES)}")
    print("  python set_state.py teammate <名前> <動いている|許可待ち|できたまま> [部屋名]")
    print("  python set_state.py cursor <名前> <running|finished|動いている|許可待ち|できたまま> [branch] [pr_url]")
    print("  python set_state.py instruct <部屋名> <指示文>")
    print("\n使用例:")
    print("  python set_state.py idle")
    print("  python set_state.py researching \"ナメック星で調査中...\"")
    print("  python set_state.py room 司令塔 動いている")
    print("  python set_state.py teammate 広告運用Bot 許可待ち 広告運用")
    print("  python set_state.py cursor \"オフィス実況化\" 動いている")
    print("\n部屋の url は渡したときだけ書き込みます（未指定なら空のまま。URLは捏造しません）。")
    print(f"Cursor のクリック先は {CURSOR_AGENTS_HOME} （または state に既にある cursor.com/agents/…）。")
    print("分・時間の見込みは state.json にその文言があるときだけ表示します。見積もりしません。")


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        usage()
        return 1

    verb = argv[1]
    state = load_state()

    if verb == "room":
        if len(argv) < 4:
            usage()
            return 1
        payload = {"name": argv[2], "status": argv[3]}
        if len(argv) > 4:
            payload["url"] = argv[4]
        if not patch_room(state, payload):
            print(f"無効な部屋名です: {argv[2]}")
            print(f"有効な部屋: {', '.join(GROK_ROOM_NAMES)}")
            return 1
        save_state(state)
        print(f"部屋を更新しました: {argv[2]} -> {normalize_bucket(argv[3])}")
        return 0

    if verb == "teammate":
        if len(argv) < 4:
            usage()
            return 1
        payload = {"name": argv[2], "status": argv[3]}
        if len(argv) > 4:
            payload["room"] = argv[4]
        if not patch_teammate(state, payload):
            print(f"無効な社員名です: {argv[2]}")
            print(f"有効な名前: {', '.join(TEAMMATE_NAMES)}")
            return 1
        save_state(state)
        print(f"社員を更新しました: {argv[2]} -> {normalize_bucket(argv[3])}")
        return 0

    if verb == "cursor":
        if len(argv) < 4:
            usage()
            return 1
        bucket = normalize_bucket(argv[3])
        payload = {
            "name": argv[2],
            "status": bucket,
            "lifecycle": normalize_lifecycle(argv[3], bucket),
        }
        if len(argv) > 4:
            payload["branch"] = argv[4]
        if len(argv) > 5:
            payload["prUrl"] = argv[5]
        if not patch_cursor_agent(state, payload):
            print("Cursor 行を更新できませんでした（name が必要です）")
            return 1
        save_state(state)
        print(f"Cursor作業を更新しました: {argv[2]} -> {bucket}")
        return 0

    if verb == "instruct":
        if len(argv) < 4:
            usage()
            return 1
        item = queue_instruction(state, {"room": argv[2], "text": argv[3]})
        if not item:
            print("指示をキューに入れられませんでした（実在の部屋名と本文が必要）")
            return 1
        save_state(state)
        print(f"指示を待ち行列に入れました（未実行）: {argv[2]} / {argv[3]}")
        return 0

    state_name = verb
    detail = argv[2] if len(argv) > 2 else ""
    if state_name not in VALID_STATES:
        print(f"無効な状態: {state_name}")
        print(f"有効なオプション: {', '.join(VALID_STATES)}")
        print(f"または room / teammate / cursor。バケツ: {', '.join(STATUS_BUCKETS)}")
        return 1

    state["state"] = state_name
    state["detail"] = detail
    save_state(state)
    print(f"状態を更新しました: {state_name} - {detail}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
