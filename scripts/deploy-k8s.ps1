# Deploy Daniel FTE to Kubernetes (Minikube) - Windows PowerShell version

Write-Host "🚀 Deploying Daniel FTE to Kubernetes..." -ForegroundColor Cyan

# Check if minikube is running
$minikubeStatus = minikube status 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "📦 Starting Minikube..." -ForegroundColor Yellow
    minikube start --driver=docker --memory=4096 --cpus=2
}

# Set docker env to use minikube's docker
Write-Host "🔨 Building Docker images..." -ForegroundColor Yellow
& minikube -p minikube docker-env --shell powershell | Invoke-Expression

# Build images
docker build -t daniel-fte/dashboard:latest ./dashboard
docker build -t daniel-fte/orchestrator:latest -f docker/orchestrator.Dockerfile .
docker build -t daniel-fte/social-mcp:latest ./mcp-servers/social-mcp

# Apply Kubernetes manifests
Write-Host "📋 Applying Kubernetes manifests..." -ForegroundColor Yellow
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/pvc.yaml
kubectl apply -f k8s/dashboard.yaml
kubectl apply -f k8s/orchestrator.yaml
kubectl apply -f k8s/social-mcp.yaml

# Wait for deployments
Write-Host "⏳ Waiting for deployments to be ready..." -ForegroundColor Yellow
kubectl wait --for=condition=available --timeout=300s deployment/dashboard -n daniel-fte

# Get the URL
Write-Host ""
Write-Host "✅ Deployment complete!" -ForegroundColor Green
Write-Host "🌐 Getting Dashboard URL..." -ForegroundColor Cyan
minikube service dashboard -n daniel-fte --url
Write-Host ""
Write-Host "🔑 Password: danielsecurepassfornow" -ForegroundColor Yellow
Write-Host ""
Write-Host "To view logs: kubectl logs -f deployment/dashboard -n daniel-fte"
Write-Host "To stop: kubectl delete namespace daniel-fte"
