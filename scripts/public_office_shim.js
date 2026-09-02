/* Public static host: /status + instruction queue without Flask. No posts/ads/billing. */
(function () {
    const ASSIGNEES = {
        '司令塔': 'メインAI社員',
        'AIバーチャルオフィス': '開発担当Bot2',
        '広告運用': '広告運用Bot',
        '海外EC': '開発担当Bot',
        '新規事業会議': '新規事業Bot',
        'Xマーケティング自動化': 'Xマーケティング担当Bot',
        '動画生成': '動画生成担当Bot',
        'コンサル管理': 'コンサル管理Bot',
        '新規顧客開拓': '新規顧客開拓Bot'
    };
    const STORE = 'saiyan-office-public-queued-instructions';
    const jsonHeaders = { 'Content-Type': 'application/json' };
    function loadQueued() {
        try {
            const rows = JSON.parse(localStorage.getItem(STORE) || '[]');
            return Array.isArray(rows) ? rows : [];
        } catch (e) {
            return [];
        }
    }
    function saveQueued(rows) {
        localStorage.setItem(STORE, JSON.stringify(rows.slice(-40)));
    }
    function jsonResponse(obj, status) {
        return new Response(JSON.stringify(obj), { status: status || 200, headers: jsonHeaders });
    }
    function pathOf(input) {
        const raw = typeof input === 'string' ? input : (input && input.url) || '';
        try {
            return new URL(raw, location.origin).pathname;
        } catch (e) {
            return String(raw || '').split('?')[0];
        }
    }
    const origFetch = window.fetch.bind(window);
    window.fetch = function (input, init) {
        const path = pathOf(input);
        const method = String((init && init.method) || 'GET').toUpperCase();
        if (path === '/status' || path === '/status.json') {
            return origFetch('/status.json', { cache: 'no-store' }).then(async (res) => {
                const data = await res.json();
                data.queuedInstructions = [...(data.queuedInstructions || []), ...loadQueued()];
                return jsonResponse(data);
            });
        }
        if (path === '/set_state' && method === 'POST') {
            let body = {};
            try { body = JSON.parse((init && init.body) || '{}'); } catch (e) { body = {}; }
            if (body && body.instruction) {
                const room = String(body.instruction.room || '').trim();
                const text = String(body.instruction.text || body.instruction.body || '').trim();
                const assignee = ASSIGNEES[room] || '';
                if (!room || !text || !assignee) {
                    return Promise.resolve(jsonResponse({
                        status: 'error',
                        msg: '指示を書けませんでした（部屋と本文が必要です）'
                    }, 400));
                }
                const now = new Date().toISOString();
                const item = {
                    id: String(body.instruction.id || ('pub-' + Date.now())),
                    room: room,
                    assignee_name: assignee,
                    text: text.slice(0, 200),
                    body: text.slice(0, 200),
                    queued: true,
                    executed: false,
                    delivered: false,
                    status: '許可待ち',
                    timestamp: now,
                    created_at: now,
                    source: 'public'
                };
                const rows = loadQueued();
                rows.push(item);
                saveQueued(rows);
                return Promise.resolve(jsonResponse({
                    status: 'ok',
                    msg: '「' + assignee + '」に渡しました（未実行）',
                    queuedInstruction: {
                        room: room,
                        assignee_name: assignee,
                        body: item.body,
                        timestamp: now
                    }
                }));
            }
            return Promise.resolve(jsonResponse({ status: 'ok' }));
        }
        if (path === '/yesterday-memo') {
            return Promise.resolve(jsonResponse({ success: false, msg: '昨日の日記はまだない' }));
        }
        if (path === '/agents') {
            return Promise.resolve(jsonResponse([]));
        }
        if (path === '/health') {
            return Promise.resolve(jsonResponse({ ok: true }));
        }
        if (path.indexOf('/assets/') === 0 || path.indexOf('/config/') === 0) {
            return Promise.resolve(jsonResponse({ ok: false, msg: '公開版では編集しません' }, 404));
        }
        return origFetch(input, init);
    };
})();
