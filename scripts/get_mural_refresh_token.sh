#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
ENV_FILE="${ROOT_DIR}/.env"

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "Error: .env not found at ${ENV_FILE}"
  exit 1
fi

# Load .env variables into this shell session.
set -a
# shellcheck disable=SC1090
source "${ENV_FILE}"
set +a

if [[ -z "${MURAL_CLIENT_ID:-}" || -z "${MURAL_CLIENT_SECRET:-}" ]]; then
  echo "Error: MURAL_CLIENT_ID and MURAL_CLIENT_SECRET must be set in .env"
  exit 1
fi

DEFAULT_SCOPES="murals:read murals:write rooms:read workspaces:read"
SCOPES="${MURAL_SCOPES:-$DEFAULT_SCOPES}"
SCOPES_ENCODED="${SCOPES// /%20}"

if [[ -z "${MURAL_REDIRECT_URI:-}" ]]; then
  read -r -p "Enter your OAuth redirect URI: " MURAL_REDIRECT_URI
fi

if [[ -z "${MURAL_REDIRECT_URI:-}" ]]; then
  echo "Error: redirect URI is required."
  exit 1
fi

AUTH_URL="https://app.mural.co/api/public/v1/authorization/oauth2/?client_id=${MURAL_CLIENT_ID}&redirect_uri=${MURAL_REDIRECT_URI}&scope=${SCOPES_ENCODED}&response_type=code"

echo
echo "1) Open this URL in your browser and authorize:"
echo "${AUTH_URL}"
echo

if command -v open >/dev/null 2>&1; then
  read -r -p "Open it automatically now? [Y/n] " OPEN_NOW
  OPEN_NOW="${OPEN_NOW:-Y}"
  if [[ "${OPEN_NOW}" =~ ^[Yy]$ ]]; then
    open "${AUTH_URL}"
  fi
fi

echo "2) After redirect, copy the 'code' query parameter."
read -r -p "Paste AUTH_CODE here: " AUTH_CODE

if [[ -z "${AUTH_CODE}" ]]; then
  echo "Error: auth code is required."
  exit 1
fi

echo
echo "3) Exchanging auth code for tokens..."
TOKEN_RESPONSE="$(curl -sS -X POST "https://app.mural.co/api/public/v1/authorization/oauth2/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  --data-urlencode "client_id=${MURAL_CLIENT_ID}" \
  --data-urlencode "client_secret=${MURAL_CLIENT_SECRET}" \
  --data-urlencode "redirect_uri=${MURAL_REDIRECT_URI}" \
  --data-urlencode "code=${AUTH_CODE}" \
  --data-urlencode "grant_type=authorization_code")"

if command -v jq >/dev/null 2>&1; then
  REFRESH_TOKEN="$(printf '%s' "${TOKEN_RESPONSE}" | jq -r '.refresh_token // empty')"
  ACCESS_TOKEN="$(printf '%s' "${TOKEN_RESPONSE}" | jq -r '.access_token // empty')"
else
  REFRESH_TOKEN="$(python3 -c 'import json,sys; print(json.load(sys.stdin).get("refresh_token",""))' <<< "${TOKEN_RESPONSE}" 2>/dev/null || true)"
  ACCESS_TOKEN="$(python3 -c 'import json,sys; print(json.load(sys.stdin).get("access_token",""))' <<< "${TOKEN_RESPONSE}" 2>/dev/null || true)"
fi

if [[ -z "${REFRESH_TOKEN:-}" || -z "${ACCESS_TOKEN:-}" ]]; then
  echo "Token exchange did not return expected tokens."
  echo "Raw response:"
  echo "${TOKEN_RESPONSE}"
  exit 1
fi

echo
echo "Success. Your refresh token:"
echo "${REFRESH_TOKEN}"
echo
echo "Update .env with:"
echo "MURAL_REFRESH_TOKEN=${REFRESH_TOKEN}"
