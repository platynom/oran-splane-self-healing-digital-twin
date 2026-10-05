param(
  [int]$DurationSeconds = 300,
  [string]$RunName = "flexric_kpm_pipeline",
  [string]$Service = "eMBB",
  [switch]$SkipPatch,
  [switch]$SkipTraining
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

if (-not $SkipPatch) {
  .\scripts\wsl_patch_flexric_kpm_single_subscription.ps1
}

.\scripts\wsl_flexric_monitor_longrun.ps1 -DurationSeconds $DurationSeconds -Monitor kpm

$ProjectRootWsl = (wsl.exe -d Ubuntu-22.04 -- wslpath -a "$ProjectRoot").Trim()
wsl.exe -d Ubuntu-22.04 -- bash -lc "cp -f ~/oran-lab/logs/xapp-monitor-longrun-latest.log '$ProjectRootWsl/data/telemetry/raw/flexric_xapp_longrun.log'"

Remove-Item -LiteralPath "data\telemetry\raw\flexric_xapp_longrun_metrics.log" -ErrorAction SilentlyContinue
Remove-Item -LiteralPath "outputs\flexric_xapp_longrun_decisions.jsonl" -ErrorAction SilentlyContinue

python tools\oai_metric_bridge.py --input data\telemetry\raw\flexric_xapp_longrun.log --output data\telemetry\raw\flexric_xapp_longrun_metrics.log --cell-id CELL_A --from-start --once
python tools\normalize_telemetry.py --input data\telemetry\raw\flexric_xapp_longrun.log --output outputs\flexric_xapp_longrun_normalized.csv --kind kv_log --cell-id CELL_A
python tools\stream_live_oai_to_engine.py --input data\telemetry\raw\flexric_xapp_longrun_metrics.log --output outputs\flexric_xapp_longrun_decisions.jsonl --db outputs\oran_twin.sqlite --service $Service --run-name $RunName --from-start --once
python tools\build_live_oai_run_report.py --db outputs\oran_twin.sqlite --decisions outputs\flexric_xapp_longrun_decisions.jsonl --metrics data\telemetry\raw\flexric_xapp_longrun_metrics.log --run-name $RunName --output outputs\reports\$RunName.json

if (-not $SkipTraining) {
  python tools\augment_kpm_training_scenarios.py --input outputs\flexric_xapp_longrun_normalized.csv --output data\training\$RunName`_augmented_training.csv --source-scenario $RunName --default-service $Service
  python scripts\train_self_learning_model.py --input data\training\$RunName`_augmented_training.csv --output outputs\models\$RunName`_self_learning_model.json
  python scripts\benchmark_ml_models.py --input data\training\$RunName`_augmented_training.csv --output outputs\benchmarks\$RunName`_ml_benchmark.json --holdout-column scenario --holdout-value radio_link_degradation
}

Write-Host ""
Write-Host "KPM evidence pipeline complete."
Write-Host "Report: outputs\reports\$RunName.json"
Write-Host "Metrics: data\telemetry\raw\flexric_xapp_longrun_metrics.log"
Write-Host "Decisions: outputs\flexric_xapp_longrun_decisions.jsonl"
if (-not $SkipTraining) {
  Write-Host "Training CSV: data\training\$RunName`_augmented_training.csv"
  Write-Host "Model: outputs\models\$RunName`_self_learning_model.json"
  Write-Host "Benchmark: outputs\benchmarks\$RunName`_ml_benchmark.json"
}
