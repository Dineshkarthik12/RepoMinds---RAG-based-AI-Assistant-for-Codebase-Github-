# deploy_gcp.ps1
# Usage: .\deploy_gcp.ps1 -ProjectID "repominds" -OpenRouterKey "KEY" -GitHubToken "TOKEN"

param (
    [Parameter(Mandatory=$true)]
    [string]$ProjectID,
    [Parameter(Mandatory=$true)]
    [string]$OpenRouterKey,
    [string]$GitHubToken = "",
    [string]$Region = "us-central1"
)

$ErrorActionPreference = "Continue"

Write-Host "🚀 Starting RepoMinds Deployment..."

# 1. Enable APIs
gcloud services enable artifactregistry.googleapis.com cloudbuild.googleapis.com run.googleapis.com --project="$ProjectID"

# 2. Repository Setup
$repoCheck = gcloud artifacts repositories describe repominds-repo --location="$Region" --project="$ProjectID" 2>$null
if ($null -eq $repoCheck) {
    gcloud artifacts repositories create repominds-repo --repository-format=docker --location="$Region" --description="RepoMinds Images" --project="$ProjectID"
}

# 3. Build Backend
gcloud builds submit --tag "$Region-docker.pkg.dev/$ProjectID/repominds-repo/backend:latest" --project="$ProjectID" --file Dockerfile.backend .

# 4. Deploy Backend
gcloud run deploy repominds-backend --image "$Region-docker.pkg.dev/$ProjectID/repominds-repo/backend:latest" --platform managed --region "$Region" --allow-unauthenticated --set-env-vars "OPENROUTER_API_KEY=$OpenRouterKey,GITHUB_TOKEN=$GitHubToken" --project="$ProjectID"

# 5. Get Backend URL
$BackendURL = gcloud run services describe repominds-backend --platform managed --region "$Region" --format "value(status.url)" --project="$ProjectID"
$BackendURL = $BackendURL.Trim()

# 6. Build Frontend
Set-Location ./frontend
gcloud builds submit --tag "$Region-docker.pkg.dev/$ProjectID/repominds-repo/frontend:latest" --project="$ProjectID" --file Dockerfile.frontend --substitutions="_VITE_API_BASE_URL=$BackendURL" .
Set-Location ..

# 7. Deploy Frontend
gcloud run deploy repominds-frontend --image "$Region-docker.pkg.dev/$ProjectID/repominds-repo/frontend:latest" --platform managed --region "$Region" --allow-unauthenticated --project="$ProjectID"

# 8. Final URLs
$FrontendURL = gcloud run services describe repominds-frontend --platform managed --region "$Region" --format "value(status.url)" --project="$ProjectID"
$FrontendURL = $FrontendURL.Trim()

Write-Host "✅ DEPLOYMENT COMPLETE!"
Write-Host "Frontend: $FrontendURL"
Write-Host "Backend:  $BackendURL"
