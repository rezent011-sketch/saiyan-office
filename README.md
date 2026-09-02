# 🐉 Saiyan Office

ピクセルアートの仮想オフィス。**Grok Bot の部屋（デスク）** と **Cursor Cloud Agent の作業** を、ローカル JSON の状態として表示します。

ライブの Cursor API や有料エンドポイントには接続しません。部屋名・社員名は決め打ちの実名のみで、追加の部屋や数字は捏造しません。

## 表示の約束

状態バケツ（この文言のみ）:

| バケツ | 意味 |
|---|---|
| 動いている | いま動いているデスク / 作業 |
| 許可待ち | 許可や開始待ち |
| できたまま | 終わったまま残っている |

- **デスク = Grok 部屋**（実名のみ）: 司令塔 / AIバーチャルオフィス / 広告運用 / 海外EC / 新規事業会議 / Xマーケティング自動化 / 動画生成 / コンサル管理 / 新規顧客開拓
- デスクをクリックすると、`state.json` の `url` があればその部屋へ飛びます。空なら飛びません（URL は捏造しません）。
- **動いている作業 = Cursor Cloud Agent**。クリック先は [cursor.com/agents](https://cursor.com/agents)。ローカルデータに `https://cursor.com/agents/bc-…` があるときだけその URL を使います。
- Cursor 作業は `state.json` の実作業だけを出します。サンプル行（表示確認 / 許可待ちの例 / 完了した作業の例）は出しません。
- **分・時間の見込み** は、その文言が `state.json` に書いてあるときだけ表示します。見積もりしません。

社員（実名のみ）: メインAI社員, 開発担当Bot, 開発担当Bot2, UTAGE・LINE担当Bot, TikTok LIVE切り抜きBot, クラウド環境構築Bot, 広告運用Bot, 動画生成担当Bot, Xマーケティング担当Bot, コンサル管理Bot, 新規事業Bot, 新規顧客開拓Bot, コンテンツ生成社員。指示の担当は部屋ごとに固定（例: 司令塔→メインAI社員、AIバーチャルオフィス→開発担当Bot2）。

投稿・広告・課金・決済・自動承認・支出の機能はありません。

## 開く（タップ用）

静的プレビュー（Flask なし / ライブAPIなし）:

**https://rezent011-sketch.github.io/saiyan-office/**

部屋と Cursor の表示は **ローカル / デモデータ** です。あとから実データを `state.json` に書けば UI が追従します。

開発者向けに、同じボードは `set_state.py` と `backend/app.py` でも更新できます。公開プレビューは GitHub Pages の静的ファイルです。

## 状態の更新

```bash
python3 set_state.py idle
python3 set_state.py executing "パイプライン実行中..."
python3 set_state.py room 司令塔 動いている
python3 set_state.py room 広告運用 許可待ち
python3 set_state.py teammate メインAI社員 動いている
python3 set_state.py cursor "Empty English omamori catalog" 動いている
python3 set_state.py instruct 司令塔 "状況をまとめて"
```

部屋 URL を書くときだけ渡してください（未指定なら空のままです）:

```bash
python3 set_state.py room 司令塔 動いている
# url を足す例（実在する部屋 URL を自分で書く。ここには書きません）
```

確認:

```bash
python3 scripts/test_office_board.py
bash scripts/build_pages.sh
```

## ピクセルオフィスのエリア（従来）

| 状態 | エリア |
|---|---|
| idle | カプセルコーポレーション（休憩） |
| writing | 修行場（ドキュメント作成） |
| executing | 精神と時の部屋（タスク処理） |
| researching | ナメック星（情報収集） |
| syncing | 天下一武道会（デプロイ） |
| error | フリーザの宇宙船（エラー） |

## License

MIT — Based on [Star-Office-UI](https://github.com/star-office-ui/star-office-ui)
