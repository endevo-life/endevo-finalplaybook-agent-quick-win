# Final Playbook — one-click launcher
# Starts the FastAPI backend (port 8001) and the Vite frontend (port 3200)
# each in its own window, independent of any editor/agent session.

$root = $PSScriptRoot
$py   = "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe"

Write-Host "Starting Final Playbook..." -ForegroundColor Cyan

# Backend
Start-Process powershell -ArgumentList @(
  "-NoExit", "-Command",
  "Set-Location '$root\agent'; & '$py' -m uvicorn app.main:app --port 8001"
) -WorkingDirectory "$root\agent"

# Frontend
Start-Process powershell -ArgumentList @(
  "-NoExit", "-Command",
  "Set-Location '$root\frontend'; npm run dev"
) -WorkingDirectory "$root\frontend"

Start-Sleep -Seconds 5
Write-Host ""
Write-Host "Backend : http://127.0.0.1:8001" -ForegroundColor Green
Write-Host "Frontend: http://localhost:3200"  -ForegroundColor Green
Write-Host "Admin   : http://localhost:3200/admin.html (needs ADMIN_TOKEN set)" -ForegroundColor Green
Write-Host ""
Write-Host "Open http://localhost:3200 in your browser." -ForegroundColor Yellow
Write-Host "Two new windows are running the servers. Close them to stop." -ForegroundColor Gray
