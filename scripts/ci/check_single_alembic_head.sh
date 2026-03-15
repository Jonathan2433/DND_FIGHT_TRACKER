#!/usr/bin/env bash
set -euo pipefail

heads_output=$(FLASK_APP=run.py flask db heads)
head_count=$(printf '%s\n' "$heads_output" | sed '/^\s*$/d' | wc -l | tr -d ' ')

if [ "$head_count" -ne 1 ]; then
  echo "❌ Expected exactly 1 Alembic head, found $head_count"
  echo "$heads_output"
  exit 1
fi

echo "✅ Single Alembic head detected:"
echo "$heads_output"
