$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

& "C:\Users\Admin\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" tools\oai_metric_bridge.py `
  --input data\telemetry\raw\sample_oai_runtime.log `
  --output data\telemetry\raw\live_oai_metrics.log `
  --cell-id CELL_A `
  --from-start `
  --once
