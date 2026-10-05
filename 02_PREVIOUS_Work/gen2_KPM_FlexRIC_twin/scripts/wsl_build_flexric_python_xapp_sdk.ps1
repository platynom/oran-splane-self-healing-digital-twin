$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

$ProjectRootWsl = (wsl.exe -d Ubuntu-22.04 -- wslpath -a "$ProjectRoot").Trim()
wsl.exe -d Ubuntu-22.04 -- bash -lc "mkdir -p ~/projects/oran-digital-twin/scripts && cp '$ProjectRootWsl/scripts/wsl_build_flexric_python_xapp_sdk.sh' ~/projects/oran-digital-twin/scripts/ && cd ~/projects/oran-digital-twin && chmod +x scripts/wsl_build_flexric_python_xapp_sdk.sh && scripts/wsl_build_flexric_python_xapp_sdk.sh"
