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
$origins = ($vars.ALLOWED_ORIGINS -split ",") | ForEach-Object { $_.Trim() } | Where-Object { $_ }
if ($origins -notcontains $Origin) { $origins += $Origin }
$vars.ALLOWED_ORIGINS = ($origins -join ",")
if ($SetAppBaseUrl) { $vars.APP_BASE_URL = $Origin }

# 3. Rebuild the Variables map as key=value pairs for the CLI.
$pairs = @()
foreach ($p in $vars.PSObject.Properties) { $pairs += "$($p.Name)=$($p.Value)" }
$envArg = "Variables={" + ($pairs -join ",") + "}"

# 4. Update (write env to a temp JSON to avoid CLI quoting issues with commas).
$envJson = @{ Variables = @{} }
foreach ($p in $vars.PSObject.Properties) { $envJson.Variables[$p.Name] = $p.Value }
$tmp = Join-Path $env:TEMP "mfp-lambda-env.json"
$envJson | ConvertTo-Json -Compress | Set-Content -Path $tmp -Encoding utf8

Write-Host "Updating $FunctionName CORS to allow: $Origin" -ForegroundColor Cyan
aws lambda update-function-configuration `
  --function-name $FunctionName `
  --region $Region `
  --environment "file://$tmp" | Out-Null

Remove-Item $tmp -Force
Write-Host "Done. ALLOWED_ORIGINS is now: $($vars.ALLOWED_ORIGINS)" -ForegroundColor Green
Write-Host "Wait ~30s for the Lambda to update, then retry sign-in." -ForegroundColor Gray
