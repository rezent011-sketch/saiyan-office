"""Local Grok room + Cursor Cloud Agent board (no live paid APIs).

Canonical names only. Status buckets are exact Japanese labels.
ETA is never estimated; 「分・時間の見込み」 is shown only when that
text already exists in the local state data.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

STATUS_BUCKETS = ("動いている", "許可待ち", "できたまま")

GROK_ROOM_NAMES = (
    "司令塔",
    "Xマーケティング自動化",
    "動画生成",
    "広告運用",
    "AIバーチャルオフィス",
)

TEAMMATE_NAMES = (
    "メインAI社員",
    "開発担当Bot",
    "UTAGE・LINE担当Bot",
    "TikTok LIVE切り抜きBot",
    "クラウド環境構築Bot",
    "広告運用Bot",
    "動画生成担当Bot",
    "Xマーケティング担当Bot",
    "コンサル管理Bot",
    "新規事業Bot",
    "新規顧客開拓Bot",
    "コンテンツ生成社員",
)

CURSOR_AGENTS_HOME = "https://cursor.com/agents"
ETA_LABEL = "分・時間の見込み"

_TEAMMATE_ROOMS = {
    "メインAI社員": "司令塔",
    "開発担当Bot": "AIバーチャルオフィス",
    "UTAGE・LINE担当Bot": "AIバーチャルオフィス",
    "TikTok LIVE切り抜きBot": "動画生成",
    "クラウド環境構築Bot": "AIバーチャルオフィス",
    "広告運用Bot": "広告運用",
    "動画生成担当Bot": "動画生成",
    "Xマーケティング担当Bot": "Xマーケティング自動化",
    "コンサル管理Bot": "司令塔",
    "新規事業Bot": "司令塔",
    "新規顧客開拓Bot": "司令塔",
    "コンテンツ生成社員": "動画生成",
}

_ROOM_DEFAULT_STATUS = {
    "司令塔": "動いている",
    "Xマーケティング自動化": "動いている",
    "動画生成": "できたまま",
    "広告運用": "許可待ち",
    "AIバーチャルオフィス": "動いている",
}

_LIFECYCLE_TO_BUCKET = {
    "running": "動いている",
    "finished": "できたまま",
}

_STATE_TO_BUCKET = {
    "idle": "できたまま",
    "writing": "動いている",
    "receiving": "動いている",
    "replying": "動いている",
    "researching": "動いている",
    "executing": "動いている",
    "syncing": "動いている",
    "error": "動いている",
    "pending": "許可待ち",
    "waiting": "許可待ち",
    "running": "動いている",
    "finished": "できたまま",
    "done": "できたまま",
}


def normalize_bucket(value: Any, lifecycle: Any = None) -> str:
    life = str(lifecycle or "").strip().lower()
    if life in _LIFECYCLE_TO_BUCKET:
        return _LIFECYCLE_TO_BUCKET[life]
    raw = str(value or "").strip()
    if raw in STATUS_BUCKETS:
        return raw
    mapped = _STATE_TO_BUCKET.get(raw.lower())
    if mapped:
        return mapped
    return "できたまま"


def normalize_lifecycle(value: Any, bucket: str | None = None) -> str:
    raw = str(value or "").strip().lower()
    if raw in {"running", "finished"}:
        return raw
    if bucket == "動いている":
        return "running"
    if bucket == "できたまま":
        return "finished"
    return ""


def cursor_open_url(agent: dict) -> str:
    url = str(agent.get("url") or "").strip()
    if url.startswith(CURSOR_AGENTS_HOME):
        return url
    return CURSOR_AGENTS_HOME


def eta_display(item: dict) -> str:
    """Show ETA only when 「分・時間の見込み」 is already written in local data."""
    if not isinstance(item, dict):
        return ""
    if ETA_LABEL in item:
        val = item.get(ETA_LABEL)
        if val is None:
            return ""
        text = str(val).strip()
        if not text:
            return ""
        return f"{ETA_LABEL} {text}"
    eta = item.get("eta")
    if isinstance(eta, str) and ETA_LABEL in eta:
        return eta.strip()
    return ""


def default_rooms() -> list[dict]:
    rooms = []
    for name in GROK_ROOM_NAMES:
        rooms.append({
            "id": name,
            "name": name,
            "kind": "desk",
            "status": _ROOM_DEFAULT_STATUS[name],
            "url": "",
            "teammates": [
                mate for mate, room in _TEAMMATE_ROOMS.items() if room == name
            ],
        })
    return rooms


def default_teammates() -> list[dict]:
    rows = []
    for name in TEAMMATE_NAMES:
        room = _TEAMMATE_ROOMS[name]
        rows.append({
            "id": name,
            "name": name,
            "room": room,
            "status": _ROOM_DEFAULT_STATUS.get(room, "できたまま"),
        })
    return rows


def default_cursor_agents() -> list[dict]:
    """No live Cursor API: do not invent or seed sample jobs."""
    return []


def _index_by_name(rows: list[dict], names: tuple[str, ...]) -> dict[str, dict]:
    found = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        name = str(row.get("name") or "").strip()
        if name in names:
            found[name] = row
    return found


def _sanitize_room(name: str, raw: dict | None) -> dict:
    src = raw if isinstance(raw, dict) else {}
    url = str(src.get("url") or "").strip()
    teammates = src.get("teammates")
    if not isinstance(teammates, list):
        teammates = [mate for mate, room in _TEAMMATE_ROOMS.items() if room == name]
    else:
        teammates = [str(t).strip() for t in teammates if str(t).strip() in TEAMMATE_NAMES]
    return {
        "id": name,
        "name": name,
        "kind": "desk",
        "status": normalize_bucket(src.get("status"), src.get("lifecycle")),
        "url": url,
        "teammates": teammates,
    }


def _sanitize_teammate(name: str, raw: dict | None) -> dict:
    src = raw if isinstance(raw, dict) else {}
    room = str(src.get("room") or _TEAMMATE_ROOMS.get(name, "司令塔")).strip()
    if room not in GROK_ROOM_NAMES:
        room = _TEAMMATE_ROOMS.get(name, "司令塔")
    return {
        "id": name,
        "name": name,
        "room": room,
        "status": normalize_bucket(src.get("status"), src.get("lifecycle")),
    }


def _sanitize_cursor_agent(raw: dict) -> dict | None:
    if not isinstance(raw, dict):
        return None
    name = str(raw.get("name") or "").strip()
    title = str(raw.get("title") or "").strip()
    if not name and not title:
        return None
    bucket = normalize_bucket(raw.get("status"), raw.get("lifecycle"))
    lifecycle = normalize_lifecycle(raw.get("lifecycle"), bucket)
    url = str(raw.get("url") or "").strip()
    if url and not url.startswith(CURSOR_AGENTS_HOME):
        url = ""
    row = {
        "name": name,
        "title": title,
        "status": bucket,
        "lifecycle": lifecycle,
        "branch": str(raw.get("branch") or "").strip(),
        "prUrl": str(raw.get("prUrl") or raw.get("pr_url") or "").strip(),
        "url": url,
        "sample": bool(raw.get("sample")) or name.startswith("サンプル"),
    }
    if ETA_LABEL in raw:
        row[ETA_LABEL] = raw.get(ETA_LABEL)
    return row


def ensure_office_board(state: dict) -> bool:
    """Fill canonical rooms/teammates/sample Cursor rows if missing. Returns True if mutated."""
    if not isinstance(state, dict):
        return False
    changed = False

    if state.get("dataSource") not in {"local", "local-demo"}:
        state["dataSource"] = "local-demo"
        changed = True

    if "liveCursorApi" not in state:
        state["liveCursorApi"] = False
        changed = True

    rooms_in = state.get("grokRooms")
    if not isinstance(rooms_in, list):
        state["grokRooms"] = default_rooms()
        changed = True
    else:
        by_name = _index_by_name(rooms_in, GROK_ROOM_NAMES)
        cleaned = [_sanitize_room(name, by_name.get(name)) for name in GROK_ROOM_NAMES]
        if cleaned != rooms_in:
            state["grokRooms"] = cleaned
            changed = True

    mates_in = state.get("teammates")
    if not isinstance(mates_in, list):
        state["teammates"] = default_teammates()
        changed = True
    else:
        by_name = _index_by_name(mates_in, TEAMMATE_NAMES)
        cleaned = [_sanitize_teammate(name, by_name.get(name)) for name in TEAMMATE_NAMES]
        if cleaned != mates_in:
            state["teammates"] = cleaned
            changed = True

    agents_in = state.get("cursorAgents")
    if not isinstance(agents_in, list):
        state["cursorAgents"] = default_cursor_agents()
        changed = True
    else:
        cleaned = []
        for raw in agents_in:
            row = _sanitize_cursor_agent(raw)
            if row and not row.get("sample"):
                cleaned.append(row)
        if cleaned != agents_in:
            state["cursorAgents"] = cleaned
            changed = True

    if not isinstance(state.get("queuedInstructions"), list):
        state["queuedInstructions"] = []
        changed = True

    return changed


def queue_instruction(state: dict, payload: dict) -> dict | None:
    """Store a desk instruction locally. Never executes posting/ads/billing."""
    ensure_office_board(state)
    if not isinstance(payload, dict):
        return None
    room = str(payload.get("room") or "").strip()
    text = str(payload.get("text") or "").strip()
    if room not in GROK_ROOM_NAMES or not text:
        return None
    item = {
        "id": str(payload.get("id") or f"q-{int(datetime.now().timestamp() * 1000)}"),
        "room": room,
        "text": text[:200],
        "status": "許可待ち",
        "queued": True,
        "executed": False,
        "source": "local",
        "created_at": datetime.now().isoformat(),
    }
    rows = state.setdefault("queuedInstructions", [])
    if not isinstance(rows, list):
        rows = []
        state["queuedInstructions"] = rows
    if not any(r.get("id") == item["id"] for r in rows if isinstance(r, dict)):
        rows.append(item)
    return item


def patch_room(state: dict, payload: dict) -> bool:
    ensure_office_board(state)
    name = str(payload.get("name") or "").strip()
    if name not in GROK_ROOM_NAMES:
        return False
    for room in state["grokRooms"]:
        if room["name"] == name:
            if "status" in payload or "lifecycle" in payload:
                room["status"] = normalize_bucket(payload.get("status"), payload.get("lifecycle"))
            if "url" in payload:
                room["url"] = str(payload.get("url") or "").strip()
            if "teammates" in payload and isinstance(payload.get("teammates"), list):
                room["teammates"] = [
                    str(t).strip() for t in payload["teammates"] if str(t).strip() in TEAMMATE_NAMES
                ]
            return True
    return False


def patch_teammate(state: dict, payload: dict) -> bool:
    ensure_office_board(state)
    name = str(payload.get("name") or "").strip()
    if name not in TEAMMATE_NAMES:
        return False
    for mate in state["teammates"]:
        if mate["name"] == name:
            if "status" in payload or "lifecycle" in payload:
                mate["status"] = normalize_bucket(payload.get("status"), payload.get("lifecycle"))
            if "room" in payload:
                room = str(payload.get("room") or "").strip()
                if room in GROK_ROOM_NAMES:
                    mate["room"] = room
            return True
    return False


def patch_cursor_agent(state: dict, payload: dict) -> bool:
    ensure_office_board(state)
    name = str(payload.get("name") or "").strip()
    title = str(payload.get("title") or "").strip()
    if not name and not title:
        return False
    agents = state["cursorAgents"]
    target = next((a for a in agents if a.get("name") == name), None)
    if target is None:
        row = _sanitize_cursor_agent(payload)
        if not row:
            return False
        agents.append(row)
        return True
    merged = dict(target)
    merged.update({k: v for k, v in payload.items() if v is not None})
    cleaned = _sanitize_cursor_agent(merged)
    if not cleaned:
        return False
    target.clear()
    target.update(cleaned)
    return True


def public_board(state: dict) -> dict:
    ensure_office_board(state)
    rooms = []
    for room in state.get("grokRooms", []):
        rooms.append({
            **room,
            "eta": eta_display(room),
        })
    teammates = list(state.get("teammates", []))
    agents = []
    for agent in state.get("cursorAgents", []):
        if agent.get("sample"):
            continue
        agents.append({
            **agent,
            "openUrl": cursor_open_url(agent),
            "eta": eta_display(agent),
        })
    return {
        "dataSource": state.get("dataSource", "local-demo"),
        "liveCursorApi": False,
        "buckets": list(STATUS_BUCKETS),
        "grokRooms": rooms,
        "teammates": teammates,
        "cursorAgents": agents,
        "queuedInstructions": list(state.get("queuedInstructions") or []),
        "liveApiNote": "Cursor / Grok ライブAPI未接続。デスクは実在の部屋。Cursor作業は未接続のため非表示。",
    }
