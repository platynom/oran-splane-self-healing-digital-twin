$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

python tools\stream_live_oai_to_engine.py `
  --input data\telemetry\raw\live_oai_metrics.log `
  --output outputs\live_oai_decisions.jsonl `
  --db outputs\oran_twin.sqlite `
  --service eMBB `
  --run-name live_oai_stream `
  --poll 1
