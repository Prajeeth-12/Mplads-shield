Write-Host "=== MPLAD-SHIELD: Full Stack Startup ===" -ForegroundColor Cyan

Write-Host "[1/3] Seeding database..."
python data/seed.py
if ($LASTEXITCODE -ne 0) { Write-Host "ERROR: Seeding failed" -ForegroundColor Red; exit 1 }

Write-Host "[2/3] Running ML pipeline..."
python pipeline/run_pipeline.py
if ($LASTEXITCODE -ne 0) { Write-Host "ERROR: Pipeline failed" -ForegroundColor Red; exit 1 }

Write-Host "[3/3] Starting services..."

Write-Host "  Starting API server on :8000..."
$api = Start-Process -NoNewWindow -PassThru -FilePath "python" -ArgumentList "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"

Write-Host "  Starting frontend on :5173..."
$fe = Start-Process -NoNewWindow -PassThru -FilePath "cmd.exe" -ArgumentList "/c", "cd frontend && npm run dev"

Write-Host ""
Write-Host "=== MPLAD-SHIELD Ready ===" -ForegroundColor Green
Write-Host "  API:  http://localhost:8000/docs"
Write-Host "  UI:   http://localhost:5173"
Write-Host "  Press Ctrl+C to stop"
Write-Host ""

try {
    Wait-Process -Id $api.Id, $fe.Id
} finally {
    if ($api -and !$api.HasExited) { Stop-Process -Id $api.Id -ErrorAction SilentlyContinue }
    if ($fe -and !$fe.HasExited) { Stop-Process -Id $fe.Id -ErrorAction SilentlyContinue }
}
