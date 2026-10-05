$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

$ProjectRootWsl = (wsl.exe -d Ubuntu-22.04 -- wslpath -a "$ProjectRoot").Trim()
wsl.exe -d Ubuntu-22.04 -- bash -lc "mkdir -p ~/projects/oran-digital-twin/scripts && cp '$ProjectRootWsl/scripts/wsl_flexric_monitor_smoke.sh' ~/projects/oran-digital-twin/scripts/ && cd ~/projects/oran-digital-twin && chmod +x scripts/wsl_flexric_monitor_smoke.sh && scripts/wsl_flexric_monitor_smoke.sh"
