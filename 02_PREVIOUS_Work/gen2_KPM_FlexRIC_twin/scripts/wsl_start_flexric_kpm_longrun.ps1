$ErrorActionPreference = "Stop"

$ProjectInWsl = "$HOME/projects/oran-digital-twin"
$Command = "cd ~/projects/oran-digital-twin && chmod +x scripts/wsl_flexric_kpm_smoke.sh && ./scripts/wsl_flexric_kpm_smoke.sh"

Write-Host "Starting WSL FlexRIC KPM smoke run..."
Write-Host "This verifies Near-RT RIC + emulated E2 node KPM setup. It is short by design."
wsl.exe -d Ubuntu-22.04 -- bash -lc $Command
