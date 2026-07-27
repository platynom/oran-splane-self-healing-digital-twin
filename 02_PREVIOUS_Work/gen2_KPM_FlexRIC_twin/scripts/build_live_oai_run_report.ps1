$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

python tools\build_live_oai_run_report.py `
  --db outputs\oran_twin.sqlite `
  --decisions outputs\live_oai_decisions.jsonl `
  --metrics data\telemetry\raw\live_oai_metrics.log `
  --run-name live_oai_stream `
  --output outputs\reports\live_oai_run_report.json
