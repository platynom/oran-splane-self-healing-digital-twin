#!/bin/sh
# Container start: sync the schema, load the derived dataset on first start only, then serve.
set -e
npx prisma db push --skip-generate
npx tsx scripts/ingest.ts --if-empty
exec npx next start -p "${PORT:-3000}"
