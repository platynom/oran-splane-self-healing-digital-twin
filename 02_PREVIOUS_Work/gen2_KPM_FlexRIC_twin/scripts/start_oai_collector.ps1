$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

& "C:\Users\Admin\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" tools\live_oai_collector.py `
  --input data\telemetry\raw\live_oai_metrics.log `
  --output data\telemetry\live_oai_feed.csv `
  --cell-id CELL_A `
  --poll 1 `
  --from-start
