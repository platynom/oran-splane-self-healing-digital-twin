param(
    [string]$DatasetRoot = "E:\dataset-kpm",
    [string]$Output = "data/training/open_ran_kpm_training_dataset.csv",
    [string]$ModelOutput = "outputs/models/open_ran_kpm_self_learning_model.json",
    [int]$MaxFiles = 120,
    [int]$SampleEvery = 10,
    [int]$MaxRows = 50000
)

$ErrorActionPreference = "Stop"

python tools/import_openran_kpm_dataset.py `
    --dataset-root $DatasetRoot `
    --output $Output `
    --max-files $MaxFiles `
    --sample-every $SampleEvery `
    --max-rows $MaxRows

python scripts/train_self_learning_model.py --input $Output --output $ModelOutput

Write-Host ""
Write-Host "Imported Open RAN KPM subset: $Output"
Write-Host "Trained model artifact: $ModelOutput"
