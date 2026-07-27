$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

$path = "data\telemetry\raw\live_oai_metrics.log"
New-Item -ItemType Directory -Force -Path (Split-Path $path) | Out-Null

$stamp = Get-Date -Format "yyyy-MM-ddTHH:mm:ss"
Add-Content -Path $path -Value "$stamp CELL_F dl_prb_usage_pct=93 ul_prb_usage_pct=86 dl_bler_pct=4.2 sinr_db=13.8 pdcp_throughput_mbps=66.5 gnb_to_upf_rtt_ms=9.4 handover_fail_pct=4.8"
Write-Host "Appended sample OAI raw metric line to $path"
