#!/bin/bash

# 🚀 Simple Deployment Script for AI Absence & SOW System
# This is a basic deployment script - DevOps should customize as needed

set -e

# Configuration
NAMESPACE="ai-absence-sow"
REGISTRY_URL="${REGISTRY_URL:-your-registry-url}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
DATABASE_TYPE="${DATABASE_TYPE:-postgresql}"  # postgresql or oracle

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_step "Checking prerequisites..."
    
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed"
        exit 1
    fi
    
    if ! command -v docker &> /dev/null; then
        log_error "docker is not installed"
        exit 1
    fi
    
    log_info "Prerequisites check passed"
}

# Build Docker images
build_images() {
    log_step "Building Docker images for $DATABASE_TYPE..."
    
    # Frontend (same for both databases)
    log_info "Building frontend image..."
    docker build -f docker/frontend/Dockerfile -t ai-absence-frontend:${IMAGE_TAG} .
    
    if [[ "$DATABASE_TYPE" == "oracle" ]]; then
        # Oracle-specific builds
        log_info "Building backend image with Oracle support..."
        docker build -f docker/backend-oracle/Dockerfile -t ai-absence-backend-oracle:${IMAGE_TAG} .
        
        log_info "Building absence service image with Oracle support..."
        docker build -f docker/absence-service-oracle/Dockerfile -t ai-absence-service-oracle:${IMAGE_TAG} .
    else
        # PostgreSQL builds (default)
        log_info "Building backend image..."
        docker build -f docker/backend/Dockerfile -t ai-absence-backend:${IMAGE_TAG} .
        
        log_info "Building absence service image..."
        docker build -f docker/absence-service/Dockerfile -t ai-absence-service:${IMAGE_TAG} .
    fi
    
    log_info "All images built successfully for $DATABASE_TYPE"
}

# Tag and push images (if registry is configured)
push_images() {
    if [[ "$REGISTRY_URL" != "your-registry-url" ]]; then
        log_step "Tagging and pushing images to registry..."
        
        # Tag images
        docker tag ai-absence-frontend:${IMAGE_TAG} ${REGISTRY_URL}/ai-absence-frontend:${IMAGE_TAG}
        docker tag ai-absence-backend:${IMAGE_TAG} ${REGISTRY_URL}/ai-absence-backend:${IMAGE_TAG}
        docker tag ai-absence-service:${IMAGE_TAG} ${REGISTRY_URL}/ai-absence-service:${IMAGE_TAG}
        
        # Push images
        docker push ${REGISTRY_URL}/ai-absence-frontend:${IMAGE_TAG}
        docker push ${REGISTRY_URL}/ai-absence-backend:${IMAGE_TAG}
        docker push ${REGISTRY_URL}/ai-absence-service:${IMAGE_TAG}
        
        log_info "Images pushed to registry"
    else
        log_warn "Registry URL not configured, skipping image push"
        log_warn "Set REGISTRY_URL environment variable to push images"
    fi
}

# Update Kubernetes manifests with registry URLs
update_manifests() {
    if [[ "$REGISTRY_URL" != "your-registry-url" ]]; then
        log_step "Updating Kubernetes manifests with registry URLs..."
        
        # Update image references in deployment files
        sed -i.bak "s|ai-absence-frontend:latest|${REGISTRY_URL}/ai-absence-frontend:${IMAGE_TAG}|g" k8s-manifests/*-deployment.yaml
        sed -i.bak "s|ai-absence-backend:latest|${REGISTRY_URL}/ai-absence-backend:${IMAGE_TAG}|g" k8s-manifests/*-deployment.yaml
        sed -i.bak "s|ai-absence-service:latest|${REGISTRY_URL}/ai-absence-service:${IMAGE_TAG}|g" k8s-manifests/*-deployment.yaml
        
        log_info "Manifests updated with registry URLs"
    else
        log_warn "Using local images (registry URL not configured)"
    fi
}

# Deploy to Kubernetes
deploy_to_kubernetes() {
    log_step "Deploying to Kubernetes with $DATABASE_TYPE database..."
    
    # Create namespace
    kubectl apply -f k8s-manifests/namespace.yaml
    
    if [[ "$DATABASE_TYPE" == "oracle" ]]; then
        # Oracle deployment
        log_info "Deploying Oracle configuration..."
        
        # Apply ConfigMaps and Secrets
        kubectl apply -f k8s-manifests/oracle-configmap.yaml
        
        # Check if Oracle secrets exist
        if ! kubectl get secret app-secrets-oracle -n $NAMESPACE &> /dev/null; then
            log_warn "Oracle secrets not found! Please create secrets before deployment:"
            log_warn "kubectl apply -f k8s-manifests/oracle-secrets-template.yaml"
            log_warn "Then update the secret values with actual credentials"
            read -p "Press Enter to continue after creating secrets..."
        fi
        
        # Apply Oracle database components
        kubectl apply -f k8s-manifests/oracle-database-init.yaml
        kubectl apply -f k8s-manifests/oracle-database-deployment.yaml
        
        # Wait for Oracle database to be ready
        log_info "Waiting for Oracle database to be ready (this may take several minutes)..."
        kubectl wait --for=condition=available deployment/oracle-db -n $NAMESPACE --timeout=600s
        
        # Apply Oracle application deployments
        kubectl apply -f k8s-manifests/oracle-backend-deployment.yaml
        kubectl apply -f k8s-manifests/oracle-absence-service-deployment.yaml
        kubectl apply -f k8s-manifests/frontend-deployment.yaml
        
        # Wait for deployments
        log_info "Waiting for application deployments to be ready..."
        kubectl wait --for=condition=available deployment/backend-oracle -n $NAMESPACE --timeout=300s
        kubectl wait --for=condition=available deployment/absence-service-oracle -n $NAMESPACE --timeout=300s
        kubectl wait --for=condition=available deployment/frontend -n $NAMESPACE --timeout=300s
        
    else
        # PostgreSQL deployment (default)
        log_info "Deploying PostgreSQL configuration..."
        
        # Apply ConfigMaps and Secrets
        kubectl apply -f k8s-manifests/configmap.yaml
        
        # Check if secrets exist
        if ! kubectl get secret app-secrets -n $NAMESPACE &> /dev/null; then
            log_warn "Secrets not found! Please create secrets before deployment:"
            log_warn "kubectl apply -f k8s-manifests/secrets-template.yaml"
            log_warn "Then update the secret values with actual credentials"
            read -p "Press Enter to continue after creating secrets..."
        fi
        
        # Apply database components
        kubectl apply -f k8s-manifests/database-init.yaml
        kubectl apply -f k8s-manifests/database-deployment.yaml
        
        # Wait for database to be ready
        log_info "Waiting for PostgreSQL database to be ready..."
        kubectl wait --for=condition=available deployment/postgres -n $NAMESPACE --timeout=300s
        
        # Apply application deployments
        kubectl apply -f k8s-manifests/backend-deployment.yaml
        kubectl apply -f k8s-manifests/absence-service-deployment.yaml
        kubectl apply -f k8s-manifests/frontend-deployment.yaml
        
        # Wait for deployments
        log_info "Waiting for application deployments to be ready..."
        kubectl wait --for=condition=available deployment/backend -n $NAMESPACE --timeout=300s
        kubectl wait --for=condition=available deployment/absence-service -n $NAMESPACE --timeout=300s
        kubectl wait --for=condition=available deployment/frontend -n $NAMESPACE --timeout=300s
    fi
    
    log_info "Deployment completed successfully with $DATABASE_TYPE database"
}

# Verify deployment
verify_deployment() {
    log_step "Verifying deployment..."
    
    # Check pod status
    log_info "Pod status:"
    kubectl get pods -n $NAMESPACE
    
    # Check service status
    log_info "Service status:"
    kubectl get services -n $NAMESPACE
    
    # Test health endpoints
    log_info "Testing health endpoints..."
    
    # Port forward and test backend
    kubectl port-forward -n $NAMESPACE service/backend-service 8080:5002 &
    BACKEND_PID=$!
    sleep 5
    
    if curl -f -s http://localhost:8080/api/health > /dev/null; then
        log_info "✅ Backend health check passed"
    else
        log_error "❌ Backend health check failed"
    fi
    
    kill $BACKEND_PID 2>/dev/null || true
    
    # Port forward and test absence service
    kubectl port-forward -n $NAMESPACE service/absence-service 8081:8080 &
    ABSENCE_PID=$!
    sleep 5
    
    if curl -f -s http://localhost:8081/actuator/health > /dev/null; then
        log_info "✅ Absence service health check passed"
    else
        log_error "❌ Absence service health check failed"
    fi
    
    kill $ABSENCE_PID 2>/dev/null || true
    
    log_info "Deployment verification completed"
}

# Cleanup function
cleanup() {
    # Restore original manifest files
    if ls k8s-manifests/*.bak 1> /dev/null 2>&1; then
        for file in k8s-manifests/*.bak; do
            mv "$file" "${file%.bak}"
        done
    fi
}

# Main deployment function
main() {
    log_info "🚀 Starting AI Absence & SOW System Deployment"
    log_info "=============================================="
    
    # Set trap for cleanup
    trap cleanup EXIT
    
    # Run deployment steps
    check_prerequisites
    build_images
    push_images
    update_manifests
    deploy_to_kubernetes
    verify_deployment
    
    log_info "=============================================="
    log_info "🎉 Deployment completed successfully!"
    log_info ""
    log_info "Next steps:"
    log_info "1. Configure ingress for external access (DevOps responsibility)"
    log_info "2. Set up monitoring and alerting (DevOps responsibility)"
    log_info "3. Configure backup procedures (DevOps responsibility)"
    log_info "4. Test the application thoroughly"
    log_info ""
    log_info "To access the application:"
    log_info "kubectl port-forward -n $NAMESPACE service/frontend-service 3000:80"
    log_info "Then open http://localhost:3000"
}

# Show usage
usage() {
    echo "Usage: $0 [options]"
    echo ""
    echo "Environment Variables:"
    echo "  REGISTRY_URL    Container registry URL (default: your-registry-url)"
    echo "  IMAGE_TAG       Docker image tag (default: latest)"
    echo "  DATABASE_TYPE   Database type: postgresql or oracle (default: postgresql)"
    echo ""
    echo "Examples:"
    echo "  # Deploy with PostgreSQL (default)"
    echo "  ./deploy.sh"
    echo ""
    echo "  # Deploy with Oracle database"
    echo "  DATABASE_TYPE=oracle ./deploy.sh"
    echo ""
    echo "  # Deploy with registry and Oracle"
    echo "  REGISTRY_URL=your-registry.com IMAGE_TAG=v1.0.0 DATABASE_TYPE=oracle ./deploy.sh"
    echo ""
    echo "Database Options:"
    echo "  postgresql      PostgreSQL database (default, easier setup)"
    echo "  oracle          Oracle Database XE (requires Oracle registry access)"
    echo ""
}

# Handle command line arguments
case "${1:-}" in
    -h|--help)
        usage
        exit 0
        ;;
    *)
        main "$@"
        ;;
esac