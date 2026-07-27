param(
    [string]$Output = "data/training/authentic_training_dataset.csv",
    [string]$ModelOutput = "outputs/models/authentic_self_learning_model.json"
)

$ErrorActionPreference = "Stop"

$inputs = @(
    "data/telemetry/sample_oai_like_kpis.csv",
    "data/telemetry/live_oai_feed.csv",
    "data/telemetry/raw/sample_oai_metrics.log"
) | Where-Object { Test-Path $_ }

if ($inputs.Count -eq 0) {
    throw "No local telemetry inputs found under data/telemetry."
}

$args = @("tools/build_training_dataset.py", "--output", $Output, "--source-id", "local_oai_telemetry")
foreach ($inputPath in $inputs) {
    $args += @("--input", $inputPath)
}

python @args
python scripts/train_self_learning_model.py --input $Output --output $ModelOutput

Write-Host ""
Write-Host "Built replay dataset: $Output"
Write-Host "Trained self-learning artifact: $ModelOutput"
