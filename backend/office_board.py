"""Local Grok room + Cursor Cloud Agent board (no live paid APIs).

Canonical names only. Status buckets are exact Japanese labels.
ETA is never estimated; 「分・時間の見込み」 is shown only when that
text already exists in the local state data.
"""

from __future__ import annotations

import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any

STATUS_BUCKETS = ("動いている", "許可待ち", "できたまま")

GROK_ROOM_NAMES = (
    "司令塔",
    "AIバーチャルオフィス",
    "広告運用",
    "海外EC",
    "新規事業会議",
    "Xマーケティング自動化",
    "動画生成",
    "コンサル管理",
    "新規顧客開拓",
)

ROOM_ASSIGNEES = {
    "司令塔": "メインAI社員",
    "AIバーチャルオフィス": "開発担当Bot2",
    "広告運用": "広告運用Bot",
    "海外EC": "開発担当Bot",
    "新規事業会議": "新規事業Bot",
    "Xマーケティング自動化": "Xマーケティング担当Bot",
    "動画生成": "動画生成担当Bot",
    "コンサル管理": "コンサル管理Bot",
    "新規顧客開拓": "新規顧客開拓Bot",
}

TEAMMATE_NAMES = (
    "メインAI社員",
    "開発担当Bot",
    "開発担当Bot2",
    "UTAGE・LINE担当Bot",
    "TikTok LIVE切り抜きBot",
    "動画生成担当Bot",
    "広告運用Bot",
    "新規事業Bot",
    "新規顧客開拓Bot",
    "Xマーケティング担当Bot",
    "クラウド環境構築Bot",
    "コンサル管理Bot",
    "Claude Code開発",
)

CURSOR_AGENTS_HOME = "https://cursor.com/agents"
ETA_LABEL = "分・時間の見込み"
LIVE_API_NOTE = "実況ボード（デスク＝Grok部屋 / 作業＝Cursor）"

# Real Cursor cloud agents / PRs only. Do not invent extras or ETAs.
LIVE_CURSOR_JOBS = (
    {
        "name": "Grok rooms + Cursor status on saiyan-office",
        "status": "動いている",
        "id": "bc-3356893b-3dfd-4261-92d1-fd6004956913",
        "url": "https://cursor.com/agents/bc-3356893b-3dfd-4261-92d1-fd6004956913",
        "prUrl": "https://github.com/rezent011-sketch/saiyan-office/pull/1",
    },
    {
        "name": "Empty English omamori catalog",
        "status": "動いている",
        "id": "bc-7cad7c8d-aff9-4dd4-8432-73430ad181d1",
        "url": "https://cursor.com/agents/bc-7cad7c8d-aff9-4dd4-8432-73430ad181d1",
    },
    {
        "name": "saiyan-office merge (人がmergeするまで。このPRをmergeしない)",
        "status": "許可待ち",
        "prUrl": "https://github.com/rezent011-sketch/saiyan-office/pull/1",
    },
    {
        "name": "saiyan-office GitHub Pages (権限は翔斗さん側。Pages設定は触らない)",
        "status": "許可待ち",
        "prUrl": "https://github.com/rezent011-sketch/saiyan-office/pull/1",
    },
    {
        "name": "Fix LP badges, proofs, celebrity collabs",
        "status": "できたまま",
        "prUrl": "https://github.com/rezent011-sketch/skillengine-line-tokuten-lp/pull/3",
    },
    {
        "name": "Tighten LP proof-card layout gaps",
        "status": "できたまま",
        "prUrl": "https://github.com/rezent011-sketch/skillengine-line-tokuten-lp/pull/5",
    },
    {
        "name": "Enable GitHub Pages on LP main",
        "status": "できたまま",
    },
    {
        "name": "Fix 50社 badge alignment",
        "status": "できたまま",
        "prUrl": "https://github.com/rezent011-sketch/skillengine-line-tokuten-lp/pull/2",
    },
    {
        "name": "Add Skill Engine LP image assets",
        "status": "できたまま",
        "prUrl": "https://github.com/rezent011-sketch/skillengine-line-tokuten-lp/pull/1",
    },
    {
        "name": "Rebuild Gagalot LP",
        "status": "できたまま",
        "prUrl": "https://github.com/rezent011-sketch/gagalot-line-tokuten-lp/pull/1",
    },
)
LIVE_CURSOR_NAMES = tuple(job["name"] for job in LIVE_CURSOR_JOBS)

SAMPLE_CURSOR_NAMES = {
    "サンプル: 表示確認",
    "サンプル: 許可待ちの例",
    "サンプル: 完了した作業の例",
    "表示確認",
    "許可待ちの例",
    "完了した作業の例",
    "オフィス実況化",
    "切り抜きタイトル直し",
    "海外EC（Origin待ち）",
    "LP空き直し",
    "著名人写真",
}
SAMPLE_CURSOR_MARKERS = (
    "サンプル",
    "sample/pending-demo",
    "sample/finished-demo",
    "sample/local-demo",
    "ピクセルオフィスの状態表示",
    "ローカルJSONの許可待ち表示",
    "できたままの表示確認",
)

_TEAMMATE_ROOMS = {
    "メインAI社員": "司令塔",
    "開発担当Bot": "海外EC",
    "開発担当Bot2": "AIバーチャルオフィス",
    "UTAGE・LINE担当Bot": "AIバーチャルオフィス",
    "TikTok LIVE切り抜きBot": "動画生成",
    "クラウド環境構築Bot": "AIバーチャルオフィス",
    "広告運用Bot": "広告運用",
    "動画生成担当Bot": "動画生成",
    "Xマーケティング担当Bot": "Xマーケティング自動化",
    "コンサル管理Bot": "コンサル管理",
    "新規事業Bot": "新規事業会議",
    "新規顧客開拓Bot": "新規顧客開拓",
    "Claude Code開発": "司令塔",
}

_ROOM_DEFAULT_STATUS = {name: "動いている" for name in GROK_ROOM_NAMES}

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


def _is_cursor_url(url: str) -> bool:
    return url.startswith(CURSOR_AGENTS_HOME)


def _is_github_pr_url(url: str) -> bool:
    return url.startswith("https://github.com/") and "/pull/" in url


def cursor_open_url(agent: dict) -> str:
    url = str(agent.get("url") or "").strip()
    if _is_cursor_url(url):
        return url
    pr = str(agent.get("prUrl") or agent.get("pr_url") or "").strip()
    if _is_github_pr_url(pr):
        return pr
    if _is_github_pr_url(url):
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


def room_assignee(name: str) -> str:
    return ROOM_ASSIGNEES.get(name, "")


def default_rooms() -> list[dict]:
    rooms = []
    for name in GROK_ROOM_NAMES:
        assignee = ROOM_ASSIGNEES[name]
        extra = [mate for mate, room in _TEAMMATE_ROOMS.items() if room == name and mate != assignee]
        rooms.append({
            "id": name,
            "name": name,
            "kind": "desk",
            "status": _ROOM_DEFAULT_STATUS[name],
            "url": "",
            "assignee": assignee,
            "teammates": [assignee, *extra],
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
            "status": _ROOM_DEFAULT_STATUS.get(room, "動いている"),
        })
    return rows


def default_cursor_agents() -> list[dict]:
    return [_sanitize_cursor_agent(dict(job)) for job in LIVE_CURSOR_JOBS]


def is_sample_cursor_job(raw: Any) -> bool:
    if not isinstance(raw, dict):
        return True
    name = str(raw.get("name") or "").strip()
    title = str(raw.get("title") or "").strip()
    branch = str(raw.get("branch") or "").strip()
    if raw.get("sample") or name.startswith("サンプル"):
        return True
    if name in SAMPLE_CURSOR_NAMES or title in SAMPLE_CURSOR_NAMES:
        return True
    blob = " ".join((name, title, branch, str(raw.get("url") or ""), str(raw.get("prUrl") or "")))
    return any(marker in blob for marker in SAMPLE_CURSOR_MARKERS)


def _detail_is_legacy_idle(text: str) -> bool:
    if not text or text in {".", "...", "smoke-check", "idle"}:
        return True
    # Old Desktop state.json used these leftover idle strings.
    return any(ord(ch) >= 0x4E00 and ord(ch) <= 0x9FFF for ch in text) and not any(
        "\u3040" <= ch <= "\u30ff" for ch in text
    )


def sanitize_public_detail(detail: Any, fallback: str = "待機中") -> str:
    text = str(detail or "").strip()
    if _detail_is_legacy_idle(text):
        return fallback
    return text


def instruction_outbox_path() -> Path:
    return Path(
        os.environ.get(
            "STAR_OFFICE_OUTBOX",
            str(Path(__file__).resolve().parent.parent / "outbox" / "instructions.jsonl"),
        )
    )


def delivered_outbox_path() -> Path:
    override = os.environ.get("STAR_OFFICE_DELIVERED")
    if override:
        return Path(override)
    return instruction_outbox_path().parent / "delivered.jsonl"


def append_instruction_outbox(item: dict) -> Path:
    """Append one queued instruction. Never wipes the file; the Mac app copies to delivered.jsonl."""
    path = instruction_outbox_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    room = str(item.get("room") or "").strip()
    row = {
        "room": room,
        "assignee_name": item.get("assignee_name") or room_assignee(room),
        "body": item.get("body") or item.get("text") or "",
        "timestamp": item.get("timestamp") or item.get("created_at") or datetime.now().isoformat(),
    }
    ident = str(item.get("id") or "").strip()
    if ident:
        row["id"] = ident
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    return path


def _read_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    rows: list[dict] = []
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError:
        return []
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict):
            rows.append(obj)
    return rows


def instruction_body(row: Any) -> str:
    if not isinstance(row, dict):
        return ""
    return str(row.get("body") or row.get("text") or "").strip()


def instruction_is_delivered(row: Any) -> bool:
    if not isinstance(row, dict):
        return False
    delivered = row.get("delivered")
    if delivered is True or str(delivered).strip().lower() in {"true", "1", "yes"}:
        return True
    if str(row.get("delivery") or "").strip().lower() == "delivered":
        return True
    if row.get("queued") is False and str(row.get("status") or "") == "できたまま":
        return True
    return False


def same_instruction(left: Any, right: Any) -> bool:
    if not isinstance(left, dict) or not isinstance(right, dict):
        return False
    lid = str(left.get("id") or "").strip()
    rid = str(right.get("id") or "").strip()
    if lid and rid and lid == rid:
        return True
    lroom = str(left.get("room") or "").strip()
    rroom = str(right.get("room") or "").strip()
    lbody = instruction_body(left)
    rbody = instruction_body(right)
    return bool(lroom and rroom and lbody and rbody and lroom == rroom and lbody == rbody)


def mark_instruction_delivered(item: dict) -> dict:
    item["delivered"] = True
    item["queued"] = False
    item["executed"] = False
    item["status"] = "できたまま"
    item["delivery"] = "delivered"
    if not item.get("body"):
        item["body"] = instruction_body(item)
    if not item.get("text"):
        item["text"] = instruction_body(item)
    return item


def apply_delivered_outbox(state: dict) -> bool:
    """Flip queued items that already landed in outbox/delivered.jsonl. Does not wipe instructions.jsonl."""
    if not isinstance(state, dict):
        return False
    delivered_rows = _read_jsonl(delivered_outbox_path())
    if not delivered_rows:
        return False
    rows = state.setdefault("queuedInstructions", [])
    if not isinstance(rows, list):
        rows = []
        state["queuedInstructions"] = rows
    changed = False
    for delivered in delivered_rows:
        matched = False
        for item in rows:
            if not isinstance(item, dict) or not same_instruction(item, delivered):
                continue
            matched = True
            if instruction_is_delivered(item):
                continue
            before = dict(item)
            mark_instruction_delivered(item)
            if item != before:
                changed = True
            break
        if not matched and instruction_body(delivered) and str(delivered.get("room") or "").strip():
            room = str(delivered.get("room") or "").strip()
            body = instruction_body(delivered)
            item = {
                "id": str(delivered.get("id") or f"delivered-{room}-{body}")[:120],
                "room": room,
                "assignee_name": delivered.get("assignee_name") or room_assignee(room),
                "text": body[:200],
                "body": body[:200],
                "source": "delivered-outbox",
                "created_at": delivered.get("timestamp") or delivered.get("created_at") or "",
                "timestamp": delivered.get("timestamp") or delivered.get("created_at") or "",
            }
            mark_instruction_delivered(item)
            rows.append(item)
            changed = True
    return changed


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
    assignee = ROOM_ASSIGNEES[name]
    teammates = src.get("teammates")
    if not isinstance(teammates, list):
        teammates = [mate for mate, room in _TEAMMATE_ROOMS.items() if room == name]
    else:
        teammates = [str(t).strip() for t in teammates if str(t).strip() in TEAMMATE_NAMES]
    if assignee not in teammates:
        teammates = [assignee, *teammates]
    else:
        teammates = [assignee, *[t for t in teammates if t != assignee]]
    return {
        "id": name,
        "name": name,
        "kind": "desk",
        "status": normalize_bucket(src.get("status"), src.get("lifecycle")) if src else _ROOM_DEFAULT_STATUS[name],
        "url": url,
        "assignee": assignee,
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
    pr_url = str(raw.get("prUrl") or raw.get("pr_url") or "").strip()
    if url and not _is_cursor_url(url):
        if _is_github_pr_url(url) and not pr_url:
            pr_url = url
        url = ""
    if pr_url and not _is_github_pr_url(pr_url):
        pr_url = ""
    row = {
        "name": name,
        "title": title,
        "status": bucket,
        "lifecycle": lifecycle,
        "branch": str(raw.get("branch") or "").strip(),
        "prUrl": pr_url,
        "url": url,
        "id": str(raw.get("id") or "").strip(),
        "sample": False,
    }
    if ETA_LABEL in raw:
        row[ETA_LABEL] = raw.get(ETA_LABEL)
    return row


def ensure_office_board(state: dict) -> bool:
    """Force canonical rooms/teammates/real Cursor jobs. Returns True if mutated."""
    if not isinstance(state, dict):
        return False
    changed = False

    if state.get("dataSource") != "local":
        state["dataSource"] = "local"
        changed = True

    if state.get("liveCursorApi") is not False:
        state["liveCursorApi"] = False
        changed = True

    rooms_in = state.get("grokRooms")
    by_name = _index_by_name(rooms_in, GROK_ROOM_NAMES) if isinstance(rooms_in, list) else {}
    cleaned_rooms = [_sanitize_room(name, by_name.get(name)) for name in GROK_ROOM_NAMES]
    if cleaned_rooms != rooms_in:
        state["grokRooms"] = cleaned_rooms
        changed = True

    mates_in = state.get("teammates")
    by_mate = _index_by_name(mates_in, TEAMMATE_NAMES) if isinstance(mates_in, list) else {}
    cleaned_mates = [_sanitize_teammate(name, by_mate.get(name)) for name in TEAMMATE_NAMES]
    if cleaned_mates != mates_in:
        state["teammates"] = cleaned_mates
        changed = True

    agents_in = state.get("cursorAgents")
    existing_by_name = {}
    if isinstance(agents_in, list):
        for raw in agents_in:
            if is_sample_cursor_job(raw):
                continue
            name = str((raw or {}).get("name") or "").strip()
            if name in LIVE_CURSOR_NAMES:
                existing_by_name[name] = raw
    cleaned_agents = []
    for job in LIVE_CURSOR_JOBS:
        src = dict(job)
        prev = existing_by_name.get(job["name"])
        if isinstance(prev, dict) and ETA_LABEL in prev:
            src[ETA_LABEL] = prev.get(ETA_LABEL)
        row = _sanitize_cursor_agent(src)
        if row:
            cleaned_agents.append(row)
    if cleaned_agents != agents_in:
        state["cursorAgents"] = cleaned_agents
        changed = True

    if not isinstance(state.get("queuedInstructions"), list):
        state["queuedInstructions"] = []
        changed = True

    if apply_delivered_outbox(state):
        changed = True

    return changed


def queue_instruction(state: dict, payload: dict) -> dict | None:
    """Store a desk instruction locally. Never executes posting/ads/billing/merge/Pages."""
    ensure_office_board(state)
    if not isinstance(payload, dict):
        return None
    room = str(payload.get("room") or "").strip()
    text = str(payload.get("text") or payload.get("body") or "").strip()
    if room not in GROK_ROOM_NAMES or not text:
        return None
    assignee = ROOM_ASSIGNEES[room]
    now = datetime.now().isoformat()
    item = {
        "id": str(payload.get("id") or f"q-{time.time_ns()}"),
        "room": room,
        "assignee_name": assignee,
        "text": text[:200],
        "body": text[:200],
        "status": "許可待ち",
        "queued": True,
        "executed": False,
        "source": "local",
        "created_at": now,
        "timestamp": now,
    }
    rows = state.setdefault("queuedInstructions", [])
    if not isinstance(rows, list):
        rows = []
        state["queuedInstructions"] = rows
    if not any(r.get("id") == item["id"] for r in rows if isinstance(r, dict)):
        rows.append(item)
        append_instruction_outbox(item)
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
                assignee = ROOM_ASSIGNEES[name]
                if assignee not in room["teammates"]:
                    room["teammates"] = [assignee, *room["teammates"]]
            room["assignee"] = ROOM_ASSIGNEES[name]
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
    if name not in LIVE_CURSOR_NAMES:
        return False
    agents = state["cursorAgents"]
    target = next((a for a in agents if a.get("name") == name), None)
    if target is None:
        return False
    merged = dict(target)
    merged.update({k: v for k, v in payload.items() if v is not None and k != "sample"})
    cleaned = _sanitize_cursor_agent(merged)
    if not cleaned or cleaned["name"] not in LIVE_CURSOR_NAMES:
        return False
    target.clear()
    target.update(cleaned)
    return True


def public_board(state: dict) -> dict:
    ensure_office_board(state)
    apply_delivered_outbox(state)
    rooms = []
    for room in state.get("grokRooms", []):
        rooms.append({
            **room,
            "assignee": room.get("assignee") or room_assignee(room.get("name")),
            "eta": eta_display(room),
        })
    teammates = list(state.get("teammates", []))
    agents = []
    for agent in state.get("cursorAgents", []):
        if is_sample_cursor_job(agent) or agent.get("name") not in LIVE_CURSOR_NAMES:
            continue
        agents.append({
            **agent,
            "sample": False,
            "openUrl": cursor_open_url(agent),
            "eta": eta_display(agent),
        })
    return {
        "dataSource": "local",
        "liveCursorApi": False,
        "buckets": list(STATUS_BUCKETS),
        "grokRooms": rooms,
        "teammates": teammates,
        "cursorAgents": agents,
        "queuedInstructions": list(state.get("queuedInstructions") or []),
        "liveApiNote": LIVE_API_NOTE,
        "roomAssignees": dict(ROOM_ASSIGNEES),
    }
