# 🐉 Saiyan Office

> An AI agent virtual office inspired by Dragon Ball — powered by OpenClaw

ピクセルアートの修行場で、あなたのAIエージェントたちがタスクをこなします。

## エージェント配置

| エージェント | キャラ | 担当 |
|---|---|---|
| Commander | 超戦士型（総大将） | 指揮・全体把握 |
| Builder | 王子型（開発将） | コーディング |
| Designer | 天才型（デザイン将） | UI/UX |
| Analyst | 宇宙人型（調査将） | リサーチ |

## 状態とエリア

| 状態 | エリア |
|---|---|
| idle | カプセルコーポレーション（休憩） |
| writing | 修行場（ドキュメント作成） |
| executing | 精神と時の部屋（タスク処理） |
| researching | ナメック星（情報収集） |
| syncing | 天下一武道会（デプロイ） |
| error | フリーザの宇宙船（エラー） |

---

## English

> An AI agent virtual office inspired by Dragon Ball — powered by [OpenClaw](https://openclaw.dev)

Pixel-art agents train and battle through tasks in legendary Dragon Ball locations.

### Agent Roster

| Agent | Character Type | Role |
|---|---|---|
| Commander | Super Warrior (General) | Direction & oversight |
| Builder | Prince Type (Dev General) | Coding & building |
| Designer | Genius Type (Design General) | UI/UX |
| Analyst | Alien Type (Intel General) | Research & analysis |

### States & Areas

| State | Area |
|---|---|
| idle | Capsule Corporation (resting) |
| writing | Training Ground (documentation) |
| executing | Hyperbolic Time Chamber (task processing) |
| researching | Planet Namek (information gathering) |
| syncing | World Martial Arts Tournament (deploy) |
| error | Frieza's Spaceship (error) |

---

## Setup

```bash
cd ~/Projects/saiyan-office
uv run python backend/app.py
# or
./backend/run.sh
```

## State Control

```bash
python set_state.py idle
python set_state.py executing "パイプライン実行中..."
python set_state.py error "エラー発生！"
```

## License

MIT — Based on [Star-Office-UI](https://github.com/star-office-ui/star-office-ui)
