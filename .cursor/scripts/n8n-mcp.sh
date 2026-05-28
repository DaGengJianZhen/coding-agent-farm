#!/usr/bin/env bash
# Bridge n8n Streamable HTTP MCP to stdio for Cursor (reads token from project .env).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

if [[ -z "${N8N_MCP_TOKEN:-}" ]]; then
  echo "n8n-mcp: N8N_MCP_TOKEN is not set. Add it to ${ROOT}/.env" >&2
  exit 1
fi

exec npx -y supergateway \
  --streamableHttp "https://wildmaker.app.n8n.cloud/mcp-server/http" \
  --oauth2Bearer "$N8N_MCP_TOKEN" \
  --logLevel none
