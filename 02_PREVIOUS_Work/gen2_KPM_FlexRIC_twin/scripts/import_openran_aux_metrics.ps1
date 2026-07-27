param(
    [string]$DatasetRoot = "E:\dataset-kpm",
    [string]$OutputDir = "data/training",
    [int]$MaxFiles = 240,
    [int]$MaxRowsPerFile = 5000
)

$ErrorActionPreference = "Stop"

python tools/import_openran_aux_metrics.py `
    --dataset-root $DatasetRoot `
    --output-dir $OutputDir `
    --max-files $MaxFiles `
    --max-rows-per-file $MaxRowsPerFile

Write-Host ""
Write-Host "Imported compact Open RAN app QoS and cell-load summaries into $OutputDir"
