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
  if (path === "/yesterday-memo") {
    return jsonResponse({ success: false, msg: "昨日の日記はまだない" });
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
