$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

& "C:\Users\Admin\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" tools\append_live_telemetry.py `
  --output data\telemetry\live_oai_feed.csv `
  --interval 1 `
  --samples 60 `
  --cell-id CELL_F
