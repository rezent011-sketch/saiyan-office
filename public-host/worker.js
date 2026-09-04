/* Same-origin public office API. No posts/ads/billing. Deno Deploy + Cloudflare Workers. */
const SURGE_ORIGIN = "https://saiyan-ai-virtual-office.surge.sh";
const ASSIGNEES = {
  "司令塔": "メインAI社員",
  "AIバーチャルオフィス": "開発担当Bot2",
  "広告運用": "広告運用Bot",
  "海外EC": "開発担当Bot",
  "新規事業会議": "新規事業Bot",
  "Xマーケティング自動化": "Xマーケティング担当Bot",
  "動画生成": "動画生成担当Bot",
  "コンサル管理": "コンサル管理Bot",
  "新規顧客開拓": "新規顧客開拓Bot",
};
const jsonHeaders = {
  "Content-Type": "application/json; charset=utf-8",
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type",
  "Cache-Control": "no-store",
};

let memoryRows = [];

function jsonResponse(obj, status) {
  return new Response(JSON.stringify(obj), { status: status || 200, headers: jsonHeaders });
}

async function openKv() {
  if (typeof Deno !== "undefined" && typeof Deno.openKv === "function") {
    return Deno.openKv();
  }
  return null;
}

async function loadQueued(env) {
  try {
    if (env && env.QUEUE && typeof env.QUEUE.get === "function") {
      const raw = await env.QUEUE.get("queuedInstructions", { type: "json" });
      if (Array.isArray(raw)) return raw;
    }
  } catch (_e) {}
  try {
    const kv = await openKv();
    if (kv) {
      const got = await kv.get(["queuedInstructions"]);
      if (Array.isArray(got.value)) return got.value;
    }
  } catch (_e) {}
  return Array.isArray(memoryRows) ? memoryRows : [];
}

async function persistGithub(rows, env) {
  const token = env && (env.GITHUB_TOKEN || env.GH_TOKEN);
  if (!token) return;
  const repo = (env && env.GITHUB_REPO) || "rezent011-sketch/saiyan-office";
  const path = (env && env.GITHUB_QUEUE_PATH) || "public-queue/queue.json";
  const branch = (env && env.GITHUB_BRANCH) || "cursor/grok-cursor-office-board-6913";
  const api = "https://api.github.com/repos/" + repo + "/contents/" + path;
  const headers = {
    Authorization: "Bearer " + token,
    Accept: "application/vnd.github+json",
    "User-Agent": "saiyan-office-public-queue",
  };
  let sha;
  try {
    const got = await fetch(api + "?ref=" + encodeURIComponent(branch), { headers });
    if (got.ok) {
      const data = await got.json();
      sha = data.sha;
    }
  } catch (_e) {}
  const payload = JSON.stringify({
    queuedInstructions: rows,
    updated_at: new Date().toISOString(),
  }, null, 2) + "\n";
  const content = btoa(unescape(encodeURIComponent(payload)));
  try {
    await fetch(api, {
      method: "PUT",
      headers: { ...headers, "Content-Type": "application/json" },
      body: JSON.stringify({
        message: "queue: desk instruction",
        content,
        sha,
        branch,
      }),
    });
  } catch (_e) {}
}

async function saveQueued(rows, env) {
  memoryRows = rows.slice(-80);
  try {
    if (env && env.QUEUE && typeof env.QUEUE.put === "function") {
      await env.QUEUE.put("queuedInstructions", JSON.stringify(memoryRows));
    }
  } catch (_e) {}
  try {
    const kv = await openKv();
    if (kv) await kv.set(["queuedInstructions"], memoryRows);
  } catch (_e) {}
  try {
    await persistGithub(memoryRows, env);
  } catch (_e) {}
  return memoryRows;
}

function queueInstruction(payload) {
  const room = String((payload && payload.room) || "").trim();
  const text = String((payload && (payload.body || payload.text)) || "").trim();
  const assignee = ASSIGNEES[room] || "";
  if (!room || !text || !assignee) return null;
  const now = new Date().toISOString();
  return {
    id: String((payload && payload.id) || ("pub-" + Date.now() + "-" + Math.random().toString(36).slice(2, 8))),
    room,
    assignee_name: assignee,
    text: text.slice(0, 200),
    body: text.slice(0, 200),
    queued: true,
    executed: false,
    delivered: false,
    status: "許可待ち",
    timestamp: now,
    created_at: now,
    source: "public",
  };
}

async function handleSetState(request, env) {
  let body = {};
  try {
    body = await request.json();
  } catch (_e) {
    body = {};
  }
  if (!body || typeof body !== "object") {
    return jsonResponse({ status: "error", msg: "invalid json" }, 400);
  }
  if (!body.instruction) {
    return jsonResponse({ status: "ok" });
  }
  const item = queueInstruction(body.instruction);
  if (!item) {
    return jsonResponse({ status: "error", msg: "指示を書けませんでした（部屋と本文が必要です）" }, 400);
  }
  const rows = await loadQueued(env);
  if (!rows.some((row) => row && row.id === item.id)) rows.push(item);
  await saveQueued(rows, env);
  return jsonResponse({
    status: "ok",
    msg: "「" + item.assignee_name + "」に渡しました（未実行）",
    queuedInstruction: {
      room: item.room,
      assignee_name: item.assignee_name,
      body: item.body,
      timestamp: item.timestamp,
    },
  });
}

function tokyoYmd(date) {
  return new Intl.DateTimeFormat("en-CA", {
    timeZone: "Asia/Tokyo",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(date);
}

function yesterdayTokyo(now) {
  const parts = new Intl.DateTimeFormat("en-CA", {
    timeZone: "Asia/Tokyo",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).formatToParts(now || new Date());
  const map = {};
  parts.forEach((p) => {
    if (p.type !== "literal") map[p.type] = p.value;
  });
  const today = new Date(Date.UTC(Number(map.year), Number(map.month) - 1, Number(map.day)));
  today.setUTCDate(today.getUTCDate() - 1);
  return today.toISOString().slice(0, 10);
}

function itemTokyoYmd(item) {
  if (!item || typeof item !== "object") return "";
  const raw = item.delivered_at || item.finished_at || item.updated_at || item.created_at || item.timestamp;
  if (!raw) return "";
  const d = new Date(raw);
  if (Number.isNaN(d.getTime())) return "";
  return tokyoYmd(d);
}

function buildYesterdayMemo(status) {
  const source = "https://saiyan-ai-virtual-office.rust-sauce.workers.dev/status";
  const yst = yesterdayTokyo(new Date());
  const lines = [];
  const seen = {};
  const add = (state, who, body) => {
    const text = "・" + [state, who, body].filter(Boolean).join(" ");
    if (seen[text]) return;
    seen[text] = true;
    lines.push(text);
  };
  (status.queuedInstructions || []).forEach((row) => {
    if (!row || itemTokyoYmd(row) !== yst) return;
    const body = String(row.body || row.text || "").trim();
    if (!body) return;
    const delivered = row.delivered === true || String(row.status || "") === "できたまま";
    const state = delivered ? "できたまま" : String(row.status || "許可待ち");
    if (state !== "できたまま" && state !== "動いている" && state !== "許可待ち") return;
    add(state, String(row.assignee_name || row.room || "").trim(), body);
  });
  (status.cursorAgents || []).forEach((agent) => {
    if (!agent || itemTokyoYmd(agent) !== yst) return;
    const life = String(agent.lifecycle || "").trim().toLowerCase();
    const st = String(agent.status || "").trim();
    const done = life === "finished" || st === "できたまま";
    const progress = life === "running" || st === "動いている";
    if (!done && !progress) return;
    const name = String(agent.title || agent.name || "").trim();
    if (!name) return;
    add(done ? "できたまま" : "動いている", name, String(agent.branch || "").trim());
  });
  (status.grokRooms || []).forEach((room) => {
    if (!room || itemTokyoYmd(room) !== yst) return;
    const task = String(room.task || room.currentTask || "").trim();
    if (!task) return;
    const life = String(room.lifecycle || "").trim().toLowerCase();
    const st = String(room.status || "").trim();
    const done = life === "finished" || st === "できたまま";
    const progress = life === "running" || st === "動いている";
    if (!done && !progress) return;
    add(done ? "できたまま" : "動いている", String(room.assignee || room.name || "").trim(), task);
  });
  if (lines.length) {
    return { success: true, date: yst, timezone: "Asia/Tokyo", source: source, memo: lines.join("\n"), count: lines.length };
  }
  const reasons = ["JST昨日（" + yst + "）に日付付きの完了・進行行がなかった"];
  const undatedDone = (status.cursorAgents || []).some((a) => a && !itemTokyoYmd(a) && (String(a.lifecycle || "").toLowerCase() === "finished" || String(a.status || "") === "できたまま"));
  if (undatedDone) reasons.push("cursorAgents のできたままに日付がないため昨日に含めない");
  const datedRooms = (status.grokRooms || []).some((r) => r && itemTokyoYmd(r));
  if (!datedRooms) reasons.push("部屋の完了に日付がない");
  const reason = reasons.join("。");
  return {
    success: false,
    empty: true,
    date: yst,
    timezone: "Asia/Tokyo",
    source: source,
    reason: reason,
    msg: "昨日（JST " + yst + "）の記録なし。出典 " + source + "。" + reason,
  };
}

async function handleYesterdayMemo(env) {
  let data = {};
  try {
    const res = await handleStatus(env);
    data = await res.json();
  } catch (_e) {
    data = {};
  }
  return jsonResponse(buildYesterdayMemo(data || {}));
}

async function handleStatus(env) {
  let data = {};
  try {
    const res = await fetch(SURGE_ORIGIN + "/status.json", { cache: "no-store" });
    data = await res.json();
  } catch (_e) {
    data = { officeName: "AIバーチャルオフィス" };
  }
  data.queuedInstructions = await loadQueued(env);
  return jsonResponse(data);
}

async function handleRequest(request, env) {
  const url = new URL(request.url);
  const path = url.pathname;
  if (request.method === "OPTIONS") {
    return new Response(null, { status: 204, headers: jsonHeaders });
  }
  if (path === "/set_state" && request.method === "POST") {
    return handleSetState(request, env);
  }
  if ((path === "/status" || path === "/status.json") && request.method === "GET") {
    return handleStatus(env);
  }
  if ((path === "/outbox.json" || path === "/outbox") && request.method === "GET") {
    return jsonResponse({ queuedInstructions: await loadQueued(env) });
  }
  if (path === "/health" && request.method === "GET") {
    return jsonResponse({ ok: true });
  }
  if (path === "/yesterday-memo" && request.method === "GET") {
    return handleYesterdayMemo(env);
  }
  if (path === "/agents") {
    return jsonResponse([]);
  }
  const target = SURGE_ORIGIN + (path === "/" ? "/" : path) + url.search;
  const proxied = await fetch(target, { headers: { "Accept": request.headers.get("Accept") || "*/*" } });
  const headers = new Headers(proxied.headers);
  headers.set("Access-Control-Allow-Origin", "*");
  return new Response(proxied.body, { status: proxied.status, headers });
}

if (typeof Deno !== "undefined" && typeof Deno.serve === "function") {
  Deno.serve((request) => handleRequest(request, undefined));
}

export default {
  fetch(request, env) {
    return handleRequest(request, env);
  },
};
