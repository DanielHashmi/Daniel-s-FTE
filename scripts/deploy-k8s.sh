#!/bin/bash
# Deploy Daniel FTE to Kubernetes (Minikube)

set -e

echo "🚀 Deploying Daniel FTE to Kubernetes..."

# Check if minikube is running
if ! minikube status > /dev/null 2>&1; then
    echo "📦 Starting Minikube..."
    minikube start --driver=docker --memory=4096 --cpus=2
fi

# Build images
echo "🔨 Building Docker images..."
eval $(minikube docker-env)

docker build -t daniel-fte/dashboard:latest ./dashboard
docker build -t daniel-fte/orchestrator:latest -f docker/orchestrator.Dockerfile .
docker build -t daniel-fte/social-mcp:latest ./mcp-servers/social-mcp

# Apply Kubernetes manifests
echo "📋 Applying Kubernetes manifests..."
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/pvc.yaml
kubectl apply -f k8s/dashboard.yaml
kubectl apply -f k8s/orchestrator.yaml
kubectl apply -f k8s/social-mcp.yaml

# Wait for deployments
echo "⏳ Waiting for deployments to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/dashboard -n daniel-fte

# Get the URL
DASHBOARD_URL=$(minikube service dashboard -n daniel-fte --url)
echo ""
echo "✅ Deployment complete!"
echo "🌐 Dashboard URL: $DASHBOARD_URL"
echo "🔑 Password: danielsecurepassfornow"
echo ""
echo "To view logs: kubectl logs -f deployment/dashboard -n daniel-fte"
echo "To stop: kubectl delete namespace daniel-fte"
