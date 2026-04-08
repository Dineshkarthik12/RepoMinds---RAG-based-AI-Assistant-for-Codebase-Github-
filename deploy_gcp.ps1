# deploy_gcp.ps1
# Usage: .\deploy_gcp.ps1 -ProjectID "repominds" -OpenRouterKey "KEY" -BucketName "dinesh-repominds-index" -GitHubToken "TOKEN"

param (
    [Parameter(Mandatory=$true)]
    [string]$ProjectID,
    [Parameter(Mandatory=$true)]
    [string]$OpenRouterKey,
    [Parameter(Mandatory=$true)]
    [string]$BucketName,
    [string]$GitHubToken = "",
    [string]$Region = "us-central1"
)

$ErrorActionPreference = "Continue"

Write-Host "Starting RepoMinds Deployment..."

# 1. Enable APIs
gcloud services enable artifactregistry.googleapis.com cloudbuild.googleapis.com run.googleapis.com --project="$ProjectID"

# 2. Repository Setup
$repoCheck = gcloud artifacts repositories describe repominds-repo --location="$Region" --project="$ProjectID" 2>$null
if ($null -eq $repoCheck) {
    gcloud artifacts repositories create repominds-repo --repository-format=docker --location="$Region" --description="RepoMinds Images" --project="$ProjectID"
}

# 3. Build Backend
Write-Host "Building Backend container..."
gcloud builds submit --tag "$Region-docker.pkg.dev/$ProjectID/repominds-repo/backend:latest" --project="$ProjectID" .

# 4. Deploy Backend (with Memory Persistence and Performance Boost)
Write-Host "Deploying Backend (2vCPU, 4GB RAM, 10m Timeout, GCS Link)..."
gcloud run deploy repominds-backend --image "$Region-docker.pkg.dev/$ProjectID/repominds-repo/backend:latest" --platform managed --region "$Region" --allow-unauthenticated --set-env-vars "OPENROUTER_API_KEY=$OpenRouterKey,GITHUB_TOKEN=$GitHubToken,GCS_BUCKET_NAME=$BucketName" --project="$ProjectID" --cpu=2 --memory=4Gi --timeout=600

# 5. Get Backend URL
$BackendURL = (gcloud run services describe repominds-backend --platform managed --region "$Region" --format "value(status.url)" --project="$ProjectID").Trim()
Write-Host "Backend URL: $BackendURL"

# 6. Build Frontend
Write-Host "Building Frontend container (Injecting Cloud URL)..."
Set-Location ./frontend
gcloud builds submit --config=cloudbuild.yaml --project="$ProjectID" --substitutions="_VITE_API_BASE_URL=$BackendURL,_TAG=$Region-docker.pkg.dev/$ProjectID/repominds-repo/frontend:latest" .
Set-Location ..

# 7. Deploy Frontend
Write-Host "Deploying Frontend..."
gcloud run deploy repominds-frontend --image "$Region-docker.pkg.dev/$ProjectID/repominds-repo/frontend:latest" --platform managed --region "$Region" --allow-unauthenticated --project="$ProjectID"

# 8. Final Results
$FrontendURL = (gcloud run services describe repominds-frontend --platform managed --region "$Region" --format "value(status.url)" --project="$ProjectID").Trim()

Write-Host "DEPLOYMENT COMPLETE!"
Write-Host "Dashboard: $FrontendURL"
Write-Host "API:       $BackendURL"
