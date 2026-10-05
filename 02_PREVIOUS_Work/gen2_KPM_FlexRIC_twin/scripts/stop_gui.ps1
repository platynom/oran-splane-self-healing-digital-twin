$connections = Get-NetTCPConnection -LocalAddress 127.0.0.1 -State Listen -ErrorAction SilentlyContinue |
    Where-Object { $_.LocalPort -ge 8080 -and $_.LocalPort -le 8129 }
foreach ($connection in $connections) {
    Stop-Process -Id $connection.OwningProcess -Force -ErrorAction SilentlyContinue
    Write-Host "Stopped PID=$($connection.OwningProcess) on port $($connection.LocalPort)"
}
if (-not $connections) {
    Write-Host "No GUI server running on ports 8080-8129"
}
