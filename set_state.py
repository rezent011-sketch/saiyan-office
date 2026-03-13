#!/usr/bin/env python3
"""Saiyan Officeの状態を更新するスクリプト（テストおよびエージェント連携用）。

OpenClawからの自動状態同期：SOUL.mdまたはAGENTS.mdに以下を追加：
  タスク開始前：`python3 set_state.py writing "作業内容"` を実行
  タスク完了後：`python3 set_state.py idle "待機中"` を実行
オフィスUIはこのスクリプトが書き込むstate.jsonを読み取ります。
"""

import json
import os
import sys
from datetime import datetime

STATE_FILE = os.environ.get(
    "STAR_OFFICE_STATE_FILE",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "state.json"),
)

VALID_STATES = [
    "idle",
    "writing",
    "receiving",
    "replying",
    "researching",
    "executing",
    "syncing",
    "error"
]

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "state": "idle",
        "detail": "修行中...",
        "progress": 0,
        "officeName": "Saiyan Office 🐉",
        "updated_at": datetime.now().isoformat()
    }

def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使用法: python set_state.py <state> [detail]")
        print(f"状態オプション: {', '.join(VALID_STATES)}")
        print("\n使用例:")
        print("  python set_state.py idle")
        print("  python set_state.py researching \"ナメック星で調査中...\"")
        print("  python set_state.py writing \"修行場でドキュメント作成中...\"")
        print("  python set_state.py executing \"精神と時の部屋でタスク処理中...\"")
        print("  python set_state.py syncing \"天下一武道会にデプロイ中...\"")
        print("  python set_state.py error \"フリーザの宇宙船でエラー発生！\"")
        sys.exit(1)
    
    state_name = sys.argv[1]
    detail = sys.argv[2] if len(sys.argv) > 2 else ""
    
    if state_name not in VALID_STATES:
        print(f"無効な状態: {state_name}")
        print(f"有効なオプション: {', '.join(VALID_STATES)}")
        sys.exit(1)
    
    state = load_state()
    state["state"] = state_name
    state["detail"] = detail
    state["updated_at"] = datetime.now().isoformat()
    
    save_state(state)
    print(f"状態を更新しました: {state_name} - {detail}")
