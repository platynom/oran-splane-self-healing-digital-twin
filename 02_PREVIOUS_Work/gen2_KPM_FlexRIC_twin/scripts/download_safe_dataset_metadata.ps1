$ErrorActionPreference = "Stop"

$datasetRoot = "dataset"
$sourceRoot = Join-Path $datasetRoot "open-ran-commercial-traffic-twinning"
New-Item -ItemType Directory -Force -Path $sourceRoot | Out-Null

$downloads = @(
    @{
        Url = "https://raw.githubusercontent.com/wineslab/open-ran-commercial-traffic-twinning-dataset/main/README.md"
        Out = "README.upstream.md"
    },
    @{
        Url = "https://raw.githubusercontent.com/wineslab/open-ran-commercial-traffic-twinning-dataset/main/LICENSE"
        Out = "LICENSE"
    },
    @{
        Url = "https://raw.githubusercontent.com/wineslab/open-ran-commercial-traffic-twinning-dataset/main/CITATION.cff"
        Out = "CITATION.cff"
    },
    @{
        Url = "https://github.com/wineslab/open-ran-commercial-traffic-twinning-dataset/archive/refs/heads/main.zip"
        Out = "source_metadata_repo.zip"
    }
)

foreach ($download in $downloads) {
    $target = Join-Path $sourceRoot $download.Out
    Invoke-WebRequest -Uri $download.Url -OutFile $target -UseBasicParsing
    Write-Host "Downloaded $($download.Url) -> $target"
}

Write-Host ""
Write-Host "Safe metadata download complete."
Write-Host "Large KPM/log archives are intentionally not downloaded by this script."
