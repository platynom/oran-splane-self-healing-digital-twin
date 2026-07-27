param(
  [string]$RunName = "flexric_xapp_longrun"
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

$ProjectRootWsl = (wsl.exe -d Ubuntu-22.04 -- wslpath -a "$ProjectRoot").Trim()
wsl.exe -d Ubuntu-22.04 -- bash -lc "cp -f ~/oran-lab/logs/xapp-monitor-longrun-latest.log '$ProjectRootWsl/data/telemetry/raw/flexric_xapp_longrun.log'"

Remove-Item -LiteralPath "data\telemetry\raw\flexric_xapp_longrun_metrics.log" -ErrorAction SilentlyContinue
Remove-Item -LiteralPath "outputs\flexric_xapp_longrun_decisions.jsonl" -ErrorAction SilentlyContinue

python tools\oai_metric_bridge.py --input data\telemetry\raw\flexric_xapp_longrun.log --output data\telemetry\raw\flexric_xapp_longrun_metrics.log --cell-id CELL_A --from-start --once
python tools\normalize_telemetry.py --input data\telemetry\raw\flexric_xapp_longrun.log --output outputs\flexric_xapp_longrun_normalized.csv --kind kv_log --cell-id CELL_A
python tools\stream_live_oai_to_engine.py --input data\telemetry\raw\flexric_xapp_longrun_metrics.log --output outputs\flexric_xapp_longrun_decisions.jsonl --db outputs\oran_twin.sqlite --run-name $RunName --from-start --once
python tools\build_live_oai_run_report.py --db outputs\oran_twin.sqlite --decisions outputs\flexric_xapp_longrun_decisions.jsonl --metrics data\telemetry\raw\flexric_xapp_longrun_metrics.log --run-name $RunName --output outputs\reports\flexric_xapp_longrun_report.json
