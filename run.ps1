<#
  Final Playbook — one-command local launcher.

  Starts the backend (FastAPI/uvicorn on :8001) and the frontend (Vite dev
  server) together, cleaning up any stale uvicorn first. Run from the repo root:

      ./run.ps1              # start both
      ./run.ps1 -Backend     # backend only
      ./run.ps1 -Frontend    # frontend only
      ./run.ps1 -Stop        # stop the backend it started

  Tip: add an alias so you can just type `fp` (see docs/run-alias below or
  README). Requires Python 3.12 and Node installed.
#>
param(
  [switch]$Backend,
  [switch]$Frontend,
  [switch]$Stop
)

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
$python = "C:\Users\nimmi\AppData\Local\Programs\Python\Python312\python.exe"
if (-not (Test-Path $python)) { $python = "python" }  # fall back to PATH

function Stop-Backend {
  Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
    Where-Object { $_.CommandLine -like '*uvicorn*app.main:app*' } |
    ForEach-Object { Write-Host "Stopping backend PID $($_.ProcessId)"; Stop-Process -Id $_.ProcessId -Force }
}

if ($Stop) { Stop-Backend; return }

$both = -not ($Backend -or $Frontend)

if ($Backend -or $both) {
  Stop-Backend
  Start-Sleep -Seconds 1
  Write-Host "Starting backend on http://localhost:8001 ..."
  Start-Process -FilePath $python `
    -ArgumentList "-m","uvicorn","app.main:app","--port","8001","--reload" `
    -WorkingDirectory "$root\agent" -WindowStyle Hidden `
    -RedirectStandardError "$env:TEMP\fp_backend.log"
  Start-Sleep -Seconds 5
  try {
    $h = Invoke-RestMethod "http://127.0.0.1:8001/api/health" -TimeoutSec 5
    Write-Host "  backend healthy: ok=$($h.ok)"
  } catch {
    Write-Warning "  backend not responding yet — check $env:TEMP\fp_backend.log"
  }
}

if ($Frontend -or $both) {
  Write-Host "Starting frontend (Vite) ..."
  Start-Process -FilePath "cmd.exe" `
    -ArgumentList "/c","npm run dev" `
    -WorkingDirectory "$root\frontend"
  Write-Host "  frontend starting — watch the new window for its http://localhost:517x URL"
}

Write-Host ""
Write-Host "Final Playbook is starting. Backend: http://localhost:8001  |  Frontend: see Vite window."
