# Add a frontend origin to the deployed backend's CORS allow-list, without
# dropping any other env var. Reads the Lambda's current environment, appends
# the new origin to ALLOWED_ORIGINS (and sets APP_BASE_URL), and updates.
#
# Usage (from infra/):  .\add-cors-origin.ps1 -Origin "https://d3m7jok0qoyofy.cloudfront.net"

param(
  [Parameter(Mandatory = $true)][string]$Origin,
  [string]$FunctionName = "mfp-dev-ApiFunction-f1WA02SeuD1T",
  [string]$Region = "us-east-1",
  [switch]$SetAppBaseUrl   # also point APP_BASE_URL (Stripe redirect) at this origin
)

$ErrorActionPreference = "Stop"

# 1. Read current env vars.
$vars = aws lambda get-function-configuration --function-name $FunctionName --region $Region --query "Environment.Variables" --output json | ConvertFrom-Json

# 2. Append the origin to ALLOWED_ORIGINS if not already present.
$origins = @(($vars.ALLOWED_ORIGINS -split ",") | ForEach-Object { $_.Trim() } | Where-Object { $_ })
if ($origins -notcontains $Origin) { $origins = $origins + $Origin }
$vars.ALLOWED_ORIGINS = ($origins -join ",")
if ($SetAppBaseUrl) { $vars.APP_BASE_URL = $Origin }
Write-Host "New ALLOWED_ORIGINS: $($vars.ALLOWED_ORIGINS)" -ForegroundColor Gray

# 3. Build the env JSON and write it WITHOUT a BOM (the AWS CLI rejects a BOM).
$envJson = @{ Variables = @{} }
foreach ($p in $vars.PSObject.Properties) { $envJson.Variables[$p.Name] = [string]$p.Value }
$tmp = Join-Path $env:TEMP "mfp-lambda-env.json"
$json = $envJson | ConvertTo-Json -Compress
[System.IO.File]::WriteAllText($tmp, $json, (New-Object System.Text.UTF8Encoding($false)))

# 4. Update, and FAIL LOUDLY if the CLI errors (don't print a false "Done").
Write-Host "Updating $FunctionName ..." -ForegroundColor Cyan
aws lambda update-function-configuration `
  --function-name $FunctionName `
  --region $Region `
  --environment "file://$tmp" | Out-Null
$ok = $?
Remove-Item $tmp -Force
if (-not $ok) { throw "Lambda update FAILED - CORS was not changed." }

Write-Host "Done. ALLOWED_ORIGINS is now: $($vars.ALLOWED_ORIGINS)" -ForegroundColor Green
Write-Host "Wait ~30s for the Lambda to finish updating, then retry sign-in." -ForegroundColor Gray

