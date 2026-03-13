#!/bin/bash
# MyAI 仮想オフィス状態更新スクリプト
# 使い方: ./update_office.sh <state> <detail>
# state: idle / writing / researching / executing / syncing / error

STATE=${1:-idle}
DETAIL=${2:-"待機中..."}

curl -s -X POST http://127.0.0.1:19000/set_state \
  -H "Content-Type: application/json" \
  -d "{\"state\":\"${STATE}\",\"detail\":\"${DETAIL}\"}" > /dev/null 2>&1

echo "✅ オフィス状態更新: ${STATE} - ${DETAIL}"
