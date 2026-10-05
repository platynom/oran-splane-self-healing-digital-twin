$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

$python = "C:\Users\Admin\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"

& $python tools\normalize_telemetry.py `
  --input data\telemetry\raw\sample_ping_linux.txt `
  --output data\telemetry\normalized_ping.csv `
  --cell-id CELL_A

& $python tools\normalize_telemetry.py `
  --input data\telemetry\raw\sample_iperf_udp.json `
  --output data\telemetry\normalized_iperf.csv `
  --cell-id CELL_A

& $python tools\normalize_telemetry.py `
  --input data\telemetry\raw\sample_oai_metrics.log `
  --output data\telemetry\normalized_oai_metrics.csv `
  --cell-id CELL_A

Write-Host "Normalized sample telemetry under data\telemetry\"
