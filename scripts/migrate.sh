#!/bin/bash
set -euo pipefail

if [ -z "${SUPABASE_URL:-}" ] || [ -z "${SUPABASE_SERVICE_ROLE_KEY:-}" ]; then
  echo "Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set"
  exit 1
fi

if ! command -v supabase >/dev/null 2>&1; then
  echo "Error: supabase CLI not found"
  exit 1
fi

supabase db push --db-url "$SUPABASE_URL" --password "$SUPABASE_SERVICE_ROLE_KEY"

echo "Migrations complete"
