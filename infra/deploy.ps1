# Final Playbook — backend deploy helper (Bedrock, Cognito, existing DynamoDB).
#
# Does the three things a bare `sam deploy` can't do on its own:
#   1. Syncs the repo-root knowledge-base/ INTO agent/ so it lands in the Lambda
#      package (CodeUri=agent/). Without this the rules engine 500s on startup.
#   2. Reads secrets (ADMIN_TOKEN, and the Anthropic key only if you switch back
#      to LlmBackend=anthropic) from agent/.env so nothing is typed on the CLI.
#   3. Runs sam build + sam deploy non-interactively with the correct params.
#
# Usage (from the infra/ folder):   .\deploy.ps1
# Override the frontend URL:         .\deploy.ps1 -AllowedOrigins "https://app.example.com" -AppBaseUrl "https://app.example.com"

param(
  [string]$StackName       = "mfp-dev",
  [string]$Region          = "us-east-1",
  [string]$LlmBackend      = "bedrock",
  [string]$BedrockRegion   = "us-east-1",
  [string]$BedrockModelId  = "us.meta.llama3-1-8b-instruct-v1:0",
  [string]$CognitoUserPoolId = "us-east-1_ikCfp5RAL",
  [string]$CognitoClientId   = "2hsqh99bm3l6hqj9uskbtbgdgd",
  [string]$CognitoRegion     = "us-east-1",
  [string]$AdminEmails     = "hello@endevo.life,bluesproutagency@gmail.com",
  [string]$AllowDevUpgrade = "true",   # demo: enables in-app upgrade/cancel. Set "false" for real prod.
  [string]$AllowedOrigins  = "http://localhost:3200",
  [string]$AppBaseUrl      = "http://localhost:3200"
)

$ErrorActionPreference = "Stop"
$infra = $PSScriptRoot
$root  = Split-Path $infra -Parent

# 1. Sync the knowledge base into the Lambda's CodeUri (agent/).
Write-Host "Syncing knowledge-base/ into agent/ for packaging..." -ForegroundColor Cyan
$src = Join-Path $root "knowledge-base"
$dst = Join-Path $root "agent\knowledge-base"
if (-not (Test-Path $dst)) { New-Item -ItemType Directory -Path $dst | Out-Null }
Copy-Item -Path (Join-Path $src "*") -Destination $dst -Recurse -Force

# 2. Read secrets from agent/.env (never printed).
$vars = @{}
Get-Content (Join-Path $root "agent\.env") | ForEach-Object {
  if ($_ -match '^\s*([^#][^=]+)=(.*)$') { $vars[$matches[1].Trim()] = $matches[2].Trim() }
}
$adminToken   = $vars['ADMIN_TOKEN']
$anthropicKey = if ($vars.ContainsKey('ANTHROPIC_API_KEY')) { $vars['ANTHROPIC_API_KEY'] } else { "" }
if ([string]::IsNullOrWhiteSpace($adminToken)) { throw "ADMIN_TOKEN is empty in agent/.env" }

# 3. Build + deploy.
Write-Host "Building..." -ForegroundColor Cyan
sam build
if ($LASTEXITCODE -ne 0) { throw "sam build failed" }

Write-Host "Deploying stack '$StackName'..." -ForegroundColor Cyan
sam deploy `
  --stack-name $StackName `
  --region $Region `
  --capabilities CAPABILITY_IAM `
  --resolve-s3 `
  --no-confirm-changeset `
  --parameter-overrides `
    "LlmBackend=$LlmBackend" `
    "BedrockRegion=$BedrockRegion" `
    "BedrockModelId=$BedrockModelId" `
    "AnthropicApiKey=$anthropicKey" `
    "AuthBackend=cognito" `
    "CognitoUserPoolId=$CognitoUserPoolId" `
    "CognitoClientId=$CognitoClientId" `
    "CognitoRegion=$CognitoRegion" `
    "AdminToken=$adminToken" `
    "AdminEmails=$AdminEmails" `
    "AllowDevUpgrade=$AllowDevUpgrade" `
    "AllowedOrigins=$AllowedOrigins" `
    "AppBaseUrl=$AppBaseUrl"
if ($LASTEXITCODE -ne 0) { throw "sam deploy failed" }

Write-Host ""
Write-Host "Deploy complete. Copy the ApiUrl output above and set it as VITE_API_BASE_URL for the frontend." -ForegroundColor Green
