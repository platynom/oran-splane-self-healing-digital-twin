#!/usr/bin/env bash
# Local helper: stop any running Next.js server, rebuild cleanly and start the production server on :3000.
set -euo pipefail
cd "$(dirname "$0")/.."
for pid in $(ps -eo pid,args | grep -E "[n]ext-server|[n]ext start|[n]ext dev" | awk '{print $1}'); do kill "$pid" || true; done
sleep 1
rm -rf .next
npm run build
nohup npx next start -p "${PORT:-3000}" > "${LOG:-/tmp/next-prod.log}" 2>&1 &
for i in $(seq 1 30); do curl -sf "http://localhost:${PORT:-3000}/api/progress" >/dev/null && echo "ready" && exit 0; sleep 1; done
echo "server did not become ready" >&2; exit 1
