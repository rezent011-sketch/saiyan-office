#!/usr/bin/env python3
"""Build yesterday's office log from Worker /status. Asia/Tokyo. No invented metrics."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

JST = timezone(timedelta(hours=9))
STATUS_URL = "https://saiyan-ai-virtual-office.rust-sauce.workers.dev/status"
MEMO_URL = "https://saiyan-ai-virtual-office.rust-sauce.workers.dev/yesterday-memo"


def tokyo_ymd(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(JST).strftime("%Y-%m-%d")


def yesterday_tokyo(now: datetime | None = None) -> str:
    now = now or datetime.now(timezone.utc)
    return tokyo_ymd(now.astimezone(JST) - timedelta(days=1))


def parse_iso(value: Any) -> datetime | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None


def item_tokyo_ymd(item: dict[str, Any] | None) -> str:
    if not isinstance(item, dict):
        return ""
    for key in (
        "delivered_at",
        "finished_at",
        "updated_at",
        "created_at",
        "timestamp",
    ):
        dt = parse_iso(item.get(key))
        if dt:
            return tokyo_ymd(dt)
    return ""


def _line(state: str, who: str, body: str) -> str:
    parts = [p for p in (state, who, body) if p]
    return "・" + " ".join(parts)


def collect_yesterday_lines(status: dict[str, Any], yst: str) -> list[str]:
    lines: list[str] = []
    seen: set[str] = set()

    def add(state: str, who: str, body: str) -> None:
        text = _line(state, who, body)
        if text in seen:
            return
        seen.add(text)
        lines.append(text)

    for row in status.get("queuedInstructions") or []:
        if not isinstance(row, dict) or item_tokyo_ymd(row) != yst:
            continue
        body = str(row.get("body") or row.get("text") or "").strip()
        if not body:
            continue
        delivered = row.get("delivered") is True or str(row.get("status") or "") == "できたまま"
        state = "できたまま" if delivered else str(row.get("status") or "許可待ち")
        if state not in ("できたまま", "動いている", "許可待ち"):
            continue
        who = str(row.get("assignee_name") or row.get("room") or "").strip()
        add(state, who, body)

    for agent in status.get("cursorAgents") or []:
        if not isinstance(agent, dict) or item_tokyo_ymd(agent) != yst:
            continue
        life = str(agent.get("lifecycle") or "").strip().lower()
        status_txt = str(agent.get("status") or "").strip()
        done = life == "finished" or status_txt == "できたまま"
        progress = life == "running" or status_txt == "動いている"
        if not done and not progress:
            continue
        name = str(agent.get("title") or agent.get("name") or "").strip()
        if not name:
            continue
        extra = str(agent.get("branch") or "").strip()
        add("できたまま" if done else "動いている", name, extra)

    for room in status.get("grokRooms") or []:
        if not isinstance(room, dict) or item_tokyo_ymd(room) != yst:
            continue
        task = str(room.get("task") or room.get("currentTask") or "").strip()
        if not task:
            continue
        life = str(room.get("lifecycle") or "").strip().lower()
        status_txt = str(room.get("status") or "").strip()
        done = life == "finished" or status_txt == "できたまま"
        progress = life == "running" or status_txt == "動いている"
        if not done and not progress:
            continue
        who = str(room.get("assignee") or room.get("name") or "").strip()
        add("できたまま" if done else "動いている", who, task)

    return lines


def empty_reason(status: dict[str, Any], yst: str) -> str:
    bits = [f"JST昨日（{yst}）に日付付きの完了・進行行がなかった"]
    undated_done = [
        a
        for a in (status.get("cursorAgents") or [])
        if isinstance(a, dict)
        and not item_tokyo_ymd(a)
        and (
            str(a.get("lifecycle") or "").lower() == "finished"
            or str(a.get("status") or "") == "できたまま"
        )
    ]
    if undated_done:
        bits.append("cursorAgents のできたままに日付がないため昨日に含めない")
    dated_rooms = [
        r
        for r in (status.get("grokRooms") or [])
        if isinstance(r, dict) and item_tokyo_ymd(r)
    ]
    if not dated_rooms:
        bits.append("部屋の完了に日付がない")
    return "。".join(bits)


def build_yesterday_memo(status: dict[str, Any], now: datetime | None = None) -> dict[str, Any]:
    yst = yesterday_tokyo(now)
    lines = collect_yesterday_lines(status if isinstance(status, dict) else {}, yst)
    payload: dict[str, Any] = {
        "date": yst,
        "timezone": "Asia/Tokyo",
        "source": STATUS_URL,
    }
    if lines:
        payload.update({"success": True, "memo": "\n".join(lines), "count": len(lines)})
        return payload
    reason = empty_reason(status if isinstance(status, dict) else {}, yst)
    payload.update(
        {
            "success": False,
            "empty": True,
            "reason": reason,
            "msg": f"昨日（JST {yst}）の記録なし。出典 {STATUS_URL}。{reason}",
        }
    )
    return payload
