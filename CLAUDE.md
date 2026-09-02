# CLAUDE.md

Claude Code Max がこのリポジトリを **所有者の Mac** で安全に触るためのメモ。汎用テンプレではない。オフィス機能の新規実装は、明示依頼がない限りやらない。

## これは何か

`saiyan-office` は Star-Office-UI（MIT）のフォーク。ピクセルオフィスで AI の状態を見せる。

- **デスク = 実在する Grok 部屋**（名前は決め打ち。部屋を増やしたり改名したりしない）
- **動いている作業 = 実在する Cursor Cloud Agent / PR**（サンプル行・捏造 URL・ETA 見積もりは出さない）
- **指示は部屋の担当エージェントへ**。実行しない。ローカル待ち行列だけ。

`main` はまだ Saiyan テーマの上流オフィス（Flask + Phaser）だけ。Grok/Cursor 実況ボードは **未マージの PR #1** にある。その契約はコードがそう言っている範囲で守る。PR #1 をマージしない。GitHub Pages は触らない。

## やってはいけないこと

- [PR #1](https://github.com/rezent011-sketch/saiyan-office/pull/1)（`cursor/grok-cursor-office-board-6913`, bc-3356893b）を **merge しない**。このブランチに積み増ししない。
- GitHub Pages を触らない（`.github/workflows/pages.yml`、`static-preview/`、Pages 有効化、`scripts/build_pages.sh` のデプロイ）。
- このアプリから **広告・課金・本番投稿**（X / 広告運用 / 決済 / 自動承認 / 支出）をしない。部屋名に「広告運用」があっても、広告を打つ機能ではない。
- 指示を実行しない。`outbox/instructions.jsonl`（または `state.json` の `queuedInstructions`）へ `room` / `assignee_name` / `body` / `timestamp` を1行足すだけ。担当へ渡した扱い。
- 有料・ライブの Cursor API に繋がない。`liveCursorApi` は常に false。状態はローカル `state.json` のみ。
- 部屋 URL・Cursor URL・「分・時間の見込み」を捏造しない。`state.json` に既にあるものだけ表示。
- シークレット（`.env`, `join-keys.json`, `runtime-config.json`）をコミット・貼り付けしない。
- 美術資産は非商用。商用前提で素材を増やさない。

## デスク ↔ 担当（PR #1 の `backend/office_board.py` が正）

状態バケツはこの3語だけ: `動いている` / `許可待ち` / `できたまま`。

| デスク（Grok 部屋） | 指示の担当（固定） |
|---|---|
| 司令塔 | メインAI社員 |
| AIバーチャルオフィス | 開発担当Bot2 |
| 広告運用 | 広告運用Bot |
| 海外EC | 開発担当Bot |
| 新規事業会議 | 新規事業Bot |
| Xマーケティング自動化 | Xマーケティング担当Bot |
| 動画生成 | 動画生成担当Bot |
| コンサル管理 | コンサル管理Bot |
| 新規顧客開拓 | 新規顧客開拓Bot |

社員名も決め打ち（13名）。勝手に追加しない。Cursor 行は実在の cloud agent / PR だけ。クリック先は `https://cursor.com/agents/...` か GitHub PR URL。どちらも無ければ `https://cursor.com/agents`。

## いまの `main` の形

```
backend/app.py          Flask。既定ポート 19000（STAR_BACKEND_PORT）
backend/{security,memo,store}_utils.py
frontend/index.html     Phaser 3.80.1 のオフィス（GET / がこれを返す。main は起動時キャッシュ）
frontend/game.js        ゲームループ
frontend/layout.js      1280x720・エリア座標（idle→breakroom、作業→writing、error→error）
set_state.py            state.json を書く（main は idle/writing/researching/executing/syncing/error + receiving/replying）
state.sample.json       テンプレ。実ファイル state.json は gitignore
office-agent-push.py    ゲストが /join-agent + /agent-push
SKILL.md                上流 OpenClaw 用。Star-Office のまま残っている
```

主な API: `GET /` `/health` `/status` `/agents` `/yesterday-memo`、`POST /set_state` `/join-agent` `/agent-push` `/leave-agent`。資産サイドバーは `ASSET_DRAWER_PASS`（ローカル既定 `1234`。本番では弱いと起動拒否）。

任意: `desktop-pet/`（Tauri、`?desktop=1`）、`electron-shell/`、Gemini 模様替え（`scripts/gemini_image_generate.py`、無くても看板は動く）。

`VALID_AGENT_STATES` は backend では 6 種。`set_state.py` だけ `receiving` / `replying` も受ける。エリアマップは `backend/app.py` の `STATE_TO_AREA_MAP`。

## ローカル確認（Mac / Safari）

Safari のプレビューは **`http://127.0.0.1:19000`**。`backend/app.py` の既定が 19000 なので、この URL が正。

```bash
# 初回
cp state.sample.json state.json
# 起動（どれか）
uv run python backend/app.py
./backend/run.sh
python3 backend/app.py
# 状態
python3 set_state.py executing "パイプライン実行中..."
python3 set_state.py idle
# サーバ起動後
python3 scripts/smoke_test.py --base-url http://127.0.0.1:19000
```

PR #1 作業ツリーでは `python3 scripts/test_office_board.py`（ネット不要）。`set_state.py room|teammate|cursor|instruct` はそのブランチだけ。

ハードリロードしないと Safari が古い `index.html` を残すことがある。PR #1 は GET / をディスクから毎回読む。`main` は `_INDEX_HTML_CACHE`。

## コミットしないもの

`state.json` `agents-state.json` `join-keys.json` `runtime-config.json` `.env` `outbox/*.jsonl`（`.gitkeep` 以外）ログ・pid。テンプレは `*.sample.json` と `.env.example`。

## 作業の置き場所

新しい仕事は `main` から新しいブランチ。PR #1 に載せない（ボード修正を明示されたときだけあのブランチ）。Pages 用ファイルをこのリポジトリに足さない。
