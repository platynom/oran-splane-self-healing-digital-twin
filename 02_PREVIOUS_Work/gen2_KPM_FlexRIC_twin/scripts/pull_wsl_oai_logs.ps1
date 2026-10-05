$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

$Output = "data\telemetry\raw\oai_runtime.log"
$WslLogs = @(
  "/home/oranuser/oran-lab/logs/nearRT-RIC.log",
  "/home/oranuser/oran-lab/logs/emu_agent_gnb.log",
  "/home/oranuser/oran-lab/logs/nearRT-RIC-oai.log",
  "/home/oranuser/oran-lab/logs/oai-gnb-flexric-rfsim.log"
)

New-Item -ItemType Directory -Force -Path (Split-Path $Output) | Out-Null
Set-Content -Path $Output -Value "" -Encoding utf8
foreach ($path in $WslLogs) {
  & wsl.exe -d Ubuntu-22.04 -- test -f $path
  if ($LASTEXITCODE -eq 0) {
    Add-Content -Path $Output -Value "===== $path ====="
    & wsl.exe -d Ubuntu-22.04 -- tail -n 400 $path | Add-Content -Path $Output
  }
}
Write-Host "Pulled WSL OAI/FlexRIC logs into $Output"
