#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

file_path=$(python3 -c "
import json, sys
data = json.load(sys.stdin)
print(data.get('tool_input', {}).get('file_path', ''))
")

case "$file_path" in
  */app/main.py|app/main.py)
    ;;
  *)
    exit 0
    ;;
esac

uv run python -c "
import json
from app.main import app
json.dump(app.openapi(), open('openapi.json', 'w'), indent=2, ensure_ascii=False)
"

echo "openapi.json regenerado a partir de app/main.py."
echo "docs/esquema.md puede haber quedado desactualizado: regeneralo con la skill 'describir-esquema'."
