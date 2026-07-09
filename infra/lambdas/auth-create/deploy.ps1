# Deploy the auth-create Lambda (branded sign-in email).
# Zips index.py and updates the mfp-dev-auth-create function code + env.
# Usage (from this folder):  .\deploy.ps1

$ErrorActionPreference = "Stop"
$here = $PSScriptRoot
$zip = Join-Path $here "function.zip"

if (Test-Path $zip) { Remove-Item $zip -Force }
Compress-Archive -Path (Join-Path $here "index.py") -DestinationPath $zip -Force

Write-Host "Updating function code..." -ForegroundColor Cyan
aws lambda update-function-code `
  --function-name "mfp-dev-auth-create" `
  --zip-file "fileb://$zip" `
  --region us-east-1 | Out-Null

Write-Host "Waiting for code update to settle..." -ForegroundColor Cyan
aws lambda wait function-updated --function-name "mfp-dev-auth-create" --region us-east-1

Write-Host "Setting env + bumping memory (faster cold-start = faster email)..." -ForegroundColor Cyan
aws lambda update-function-configuration `
  --function-name "mfp-dev-auth-create" `
  --memory-size 256 `
  --timeout 10 `
  --environment "Variables={FROM_EMAIL=hello@endevo.life,APP_NAME=My Final Playbook,BRAND_URL=endevo.life}" `
  --region us-east-1 | Out-Null

Remove-Item $zip -Force
Write-Host "Done. Trigger a sign-in to see the new branded email." -ForegroundColor Green
