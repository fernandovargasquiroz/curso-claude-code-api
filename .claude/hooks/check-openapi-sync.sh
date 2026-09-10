#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

tmp=$(mktemp /tmp/openapi-check-XXXXXX.json)
trap 'rm -f "$tmp"' EXIT

if ! uv run python -c "
import json
from app.main import app
json.dump(app.openapi(), open('$tmp', 'w'), indent=2, ensure_ascii=False)
" >/dev/null 2>&1; then
  echo '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"No se pudo regenerar la especificacion OpenAPI para compararla (revisa que uv sync este hecho). El commit se bloqueo por seguridad."}}'
  exit 0
fi

if diff -q openapi.json "$tmp" >/dev/null 2>&1; then
  exit 0
fi

echo '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"openapi.json no coincide con lo que genera el codigo ahora mismo. Regeneralo con el comando de la seccion \"Especificacion OpenAPI\" de README.md y agregalo al commit (git add openapi.json) antes de confirmar."}}'
exit 0
