# Deploy the frontend to AWS (S3 + CloudFront).
#
# What it does:
#   1. Deploys/updates the frontend stack (private S3 + CloudFront + HTTPS).
#   2. Builds the Vite app pointed at the live API.
#   3. Uploads dist/ to the bucket.
#   4. Invalidates the CloudFront cache so the new build shows immediately.
#   5. Prints the live URL + the exact command to allow it in backend CORS.
#
# Usage (from the infra/ folder):  .\deploy-frontend.ps1
# First CloudFront create takes ~15-20 min; later runs are fast.

param(
  [string]$StackName = "mfp-dev-frontend",
  [string]$Region    = "us-east-1",
  [string]$BucketName = "mfp-dev-frontend",
  [string]$ApiUrl    = "https://xlzj6dntz0.execute-api.us-east-1.amazonaws.com",
  # Custom domain: pass BOTH or NEITHER. Cert must be ISSUED, in us-east-1.
  #   .\deploy-frontend.ps1 -DomainName app.finalplaybook.com -CertificateArn arn:aws:acm:us-east-1:...:certificate/...
  [string]$DomainName = "",
  [string]$CertificateArn = ""
)

$ErrorActionPreference = "Stop"
$infra = $PSScriptRoot
$root  = Split-Path $infra -Parent

if (($DomainName -and -not $CertificateArn) -or ($CertificateArn -and -not $DomainName)) {
  throw "Pass -DomainName and -CertificateArn together (or neither)."
}
$overrides = @("BucketName=$BucketName")
if ($DomainName) {
  $overrides += "DomainName=$DomainName"
  $overrides += "AcmCertificateArn=$CertificateArn"
}

Write-Host "1/5  Deploying frontend stack (S3 + CloudFront)..." -ForegroundColor Cyan
aws cloudformation deploy `
  --template-file (Join-Path $infra "frontend.yaml") `
  --stack-name $StackName `
  --region $Region `
  --parameter-overrides $overrides `
  --no-fail-on-empty-changeset
if ($LASTEXITCODE -ne 0) { throw "stack deploy failed" }

# Pull outputs
$outputs = aws cloudformation describe-stacks --stack-name $StackName --region $Region --query "Stacks[0].Outputs" --output json | ConvertFrom-Json
$bucket = ($outputs | Where-Object { $_.OutputKey -eq "SiteBucketName" }).OutputValue
$distId = ($outputs | Where-Object { $_.OutputKey -eq "DistributionId" }).OutputValue
$siteUrl = ($outputs | Where-Object { $_.OutputKey -eq "SiteUrl" }).OutputValue

Write-Host "2/5  Building the frontend (API = $ApiUrl)..." -ForegroundColor Cyan
Push-Location (Join-Path $root "frontend")
$env:VITE_API_BASE_URL = $ApiUrl
npm run build
if ($LASTEXITCODE -ne 0) { Pop-Location; throw "frontend build failed" }
Pop-Location

Write-Host "3/5  Uploading to s3://$bucket ..." -ForegroundColor Cyan
# Long-cache the hashed assets, no-cache the HTML so new deploys show immediately.
aws s3 sync (Join-Path $root "frontend\dist") "s3://$bucket" --region $Region --delete `
  --cache-control "public,max-age=31536000,immutable" --exclude "*.html"
aws s3 sync (Join-Path $root "frontend\dist") "s3://$bucket" --region $Region `
  --cache-control "no-cache" --exclude "*" --include "*.html"

Write-Host "4/5  Invalidating CloudFront cache..." -ForegroundColor Cyan
aws cloudfront create-invalidation --distribution-id $distId --paths "/*" --region $Region | Out-Null

Write-Host "5/5  Done." -ForegroundColor Green
Write-Host ""
Write-Host "  LIVE URL:  $siteUrl" -ForegroundColor Green
Write-Host ""
Write-Host "  IMPORTANT - allow this URL on the backend (CORS), or API calls fail." -ForegroundColor Yellow
Write-Host "  Run this next (from the infra folder):" -ForegroundColor Yellow
$corsCmd = '.\deploy.ps1 -AllowedOrigins "http://localhost:3200,' + $siteUrl + '" -AppBaseUrl "' + $siteUrl + '"'
Write-Host "    $corsCmd" -ForegroundColor White
Write-Host ""
Write-Host "  (First CloudFront deploy can take ~15-20 min to fully propagate.)" -ForegroundColor Gray
