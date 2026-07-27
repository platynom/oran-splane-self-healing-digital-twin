param(
  [string]$RunName = "local_hardening_check",
  [int]$Duration = 60,
  [int]$Seed = 42
)

$ErrorActionPreference = "Stop"

Write-Host "Compiling Python modules..."
python -m compileall oran_twin live_backend.py run_demo.py xapp_runner.py

Write-Host "Running batch demo..."
python run_demo.py --run-name $RunName --duration $Duration --seed $Seed

Write-Host "Running xApp-style check..."
python xapp_runner.py --input "outputs\runs\$RunName\simulated_kpis.csv" --output "outputs\$RunName`_xapp.jsonl" --service eMBB

Write-Host "Checking required outputs..."
$required = @(
  "outputs\runs\$RunName\summary.json",
  "outputs\runs\$RunName\evaluation.json",
  "outputs\runs\$RunName\evaluation_report.md",
  "outputs\runs\$RunName\incident_report.md",
  "outputs\runs\$RunName\dashboard.html",
  "outputs\$RunName`_xapp.jsonl",
  "outputs\oran_twin.sqlite"
)

foreach ($path in $required) {
  if (!(Test-Path $path)) {
    throw "Missing required output: $path"
  }
}

$summary = Get-Content "outputs\runs\$RunName\summary.json" | ConvertFrom-Json
Write-Host "Validation passed."
Write-Host "Records: $($summary.records)"
Write-Host "Virtual devices: $($summary.device_population.total_devices)"
Write-Host "Unsafe actions prevented: $($summary.unsafe_actions_prevented)"
Write-Host "Mean automation safety score: $($summary.mean_automation_safety_score)"
