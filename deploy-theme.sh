#!/usr/bin/env bash
set -euo pipefail

GHOST_URL="https://robertnealan.com"
THEME_NAME="midway"

# Admin API key: id:secret
GHOST_ADMIN_API_KEY="${GHOST_ADMIN_API_KEY:?Set GHOST_ADMIN_API_KEY env var (id:secret format)}"

API_ID="${GHOST_ADMIN_API_KEY%%:*}"
API_SECRET="${GHOST_ADMIN_API_KEY##*:}"

# Build JWT token
header=$(echo -n '{"alg":"HS256","typ":"JWT","kid":"'"$API_ID"'"}' | base64 | tr -d '=' | tr '/+' '_-' | tr -d '\n')
now=$(date +%s)
payload=$(echo -n '{"iat":'"$now"',"exp":'"$((now + 300))"',"aud":"/admin/"}' | base64 | tr -d '=' | tr '/+' '_-' | tr -d '\n')
signature=$(echo -n "${header}.${payload}" | openssl dgst -sha256 -hmac "$(echo -n "$API_SECRET" | xxd -r -p)" -binary | base64 | tr -d '=' | tr '/+' '_-' | tr -d '\n')
TOKEN="${header}.${payload}.${signature}"

# Zip theme
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ZIPFILE=$(mktemp /tmp/midway-XXXXXX).zip
cd "$SCRIPT_DIR"
zip -r "$ZIPFILE" assets partials *.hbs package.json -x "node_modules/*" > /dev/null

echo "Uploading theme..."
RESPONSE=$(curl -s -w "\n%{http_code}" \
  -X POST "${GHOST_URL}/ghost/api/admin/themes/upload/" \
  -H "Authorization: Ghost ${TOKEN}" \
  -F "file=@${ZIPFILE};filename=${THEME_NAME}.zip")

HTTP_CODE=$(echo "$RESPONSE" | tail -1)
BODY=$(echo "$RESPONSE" | sed '$d')

rm -f "$ZIPFILE"

if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "201" ]; then
  echo "Theme uploaded and activated successfully."
else
  echo "Failed (HTTP ${HTTP_CODE}):"
  echo "$BODY"
  exit 1
fi
