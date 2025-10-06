#!/bin/bash

# 🚀 Complete Deployment Script for Oracle Cloud + Kubernetes
# AI Absence & SOW System - Production Deployment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DEPLOYMENT_NAME="ai-absence-sow"
NAMESPACE="ai-absence-sow"
REGISTRY_URL="your-registry-url"  # Update with your Oracle Container Registry URL

# Functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

log_step() {
    echo -e "${PURPLE}🚀 $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    log_step "Checking prerequisites..."
    
    # Check required tools
    local tools=("docker" "kubectl" "terraform" "helm")
    for tool in "${tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            log_error "$tool is not installed or not in PATH"
            exit 1
        fi
    done
    
    # Check Oracle Cloud CLI
    if ! command -v "oci" &> /dev/null; then
        log_warning "Oracle Cloud CLI not found. Please install it for full functionality."
    fi
    
    # Check environment variables
    local required_vars=("OCI_TENANCY_OCID" "OCI_USER_OCID" "OCI_FINGERPRINT" "OCI_PRIVATE_KEY_PATH" "OCI_REGION")
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var}" ]]; then
            log_error "Environment variable $var is not set"
            exit 1
        fi
    done
    
    log_success "All prerequisites met"
}

# Build Docker images
build_images() {
    log_step "Building Docker images..."
    
    cd "$PROJECT_ROOT"
    
    # Build Frontend
    log_info "Building frontend image..."
    docker build -f docker/frontend/Dockerfile -t "$REGISTRY_URL/ai-absence-sow-frontend:latest" .
    
    # Build Backend
    log_info "Building backend image..."
    docker build -f docker/backend/Dockerfile -t "$REGISTRY_URL/ai-absence-sow-backend:latest" .
    
    # Build Absence Service
    log_info "Building absence service image..."
    docker build -f docker/absence-service/Dockerfile -t "$REGISTRY_URL/ai-absence-sow-absence-service:latest" .
    
    log_success "All images built successfully"
}

# Push images to registry
push_images() {
    log_step "Pushing images to Oracle Container Registry..."
    
    # Login to Oracle Container Registry
    log_info "Logging into Oracle Container Registry..."
    echo "$OCI_AUTH_TOKEN" | docker login "$REGISTRY_URL" -u "$OCI_USERNAME" --password-stdin
    
    # Push images
    docker push "$REGISTRY_URL/ai-absence-sow-frontend:latest"
    docker push "$REGISTRY_URL/ai-absence-sow-backend:latest"
    docker push "$REGISTRY_URL/ai-absence-sow-absence-service:latest"
    
    log_success "All images pushed to registry"
}

# Deploy infrastructure with Terraform
deploy_infrastructure() {
    log_step "Deploying infrastructure with Terraform..."
    
    cd "$PROJECT_ROOT/terraform"
    
    # Initialize Terraform
    log_info "Initializing Terraform..."
    terraform init
    
    # Plan deployment
    log_info "Planning infrastructure deployment..."
    terraform plan -out=tfplan
    
    # Apply deployment
    log_info "Applying infrastructure deployment..."
    terraform apply tfplan
    
    # Get cluster credentials
    log_info "Configuring kubectl..."
    local cluster_id=$(terraform output -raw cluster_id)
    oci ce cluster create-kubeconfig --cluster-id "$cluster_id" --file ~/.kube/config --region "$OCI_REGION" --token-version 2.0.0
    
    log_success "Infrastructure deployed successfully"
}

# Deploy Kubernetes resources
deploy_kubernetes() {
    log_step "Deploying Kubernetes resources..."
    
    cd "$PROJECT_ROOT"
    
    # Create namespace
    log_info "Creating namespace..."
    kubectl apply -f k8s/namespace.yaml
    
    # Deploy secrets (update with actual values)
    log_info "Deploying secrets..."
    kubectl apply -f k8s/secrets.yaml
    
    # Deploy ConfigMaps
    log_info "Deploying ConfigMaps..."
    kubectl apply -f k8s/configmap.yaml
    
    # Deploy PersistentVolumes
    log_info "Deploying storage..."
    kubectl apply -f k8s/storage/
    
    # Deploy database
    log_info "Deploying PostgreSQL database..."
    kubectl apply -f k8s/database/
    
    # Wait for database to be ready
    log_info "Waiting for database to be ready..."
    kubectl wait --for=condition=ready pod -l app.kubernetes.io/component=database -n "$NAMESPACE" --timeout=300s
    
    # Deploy applications
    log_info "Deploying application services..."
    kubectl apply -f k8s/deployments/
    kubectl apply -f k8s/services.yaml
    
    # Wait for deployments to be ready
    log_info "Waiting for deployments to be ready..."
    kubectl wait --for=condition=available deployment --all -n "$NAMESPACE" --timeout=600s
    
    # Deploy ingress
    log_info "Deploying ingress controller..."
    kubectl apply -f k8s/ingress.yaml
    
    log_success "Kubernetes resources deployed successfully"
}

# Install monitoring stack
install_monitoring() {
    log_step "Installing monitoring stack..."
    
    # Add Helm repositories
    helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
    helm repo add grafana https://grafana.github.io/helm-charts
    helm repo update
    
    # Install Prometheus
    log_info "Installing Prometheus..."
    helm upgrade --install prometheus prometheus-community/kube-prometheus-stack \
        --namespace monitoring \
        --create-namespace \
        --set grafana.adminPassword="admin123" \
        --wait
    
    # Install Loki for log aggregation
    log_info "Installing Loki..."
    helm upgrade --install loki grafana/loki-stack \
        --namespace monitoring \
        --set grafana.enabled=false \
        --wait
    
    log_success "Monitoring stack installed successfully"
}

# Configure SSL certificates
configure_ssl() {
    log_step "Configuring SSL certificates..."
    
    # Install cert-manager
    log_info "Installing cert-manager..."
    kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml
    
    # Wait for cert-manager to be ready
    kubectl wait --for=condition=available deployment --all -n cert-manager --timeout=300s
    
    # Apply cluster issuer
    kubectl apply -f k8s/ingress.yaml
    
    log_success "SSL certificates configured successfully"
}

# Run health checks
health_checks() {
    log_step "Running health checks..."
    
    # Check pod status
    log_info "Checking pod status..."
    kubectl get pods -n "$NAMESPACE"
    
    # Check service endpoints
    log_info "Checking service endpoints..."
    kubectl get endpoints -n "$NAMESPACE"
    
    # Test application endpoints
    log_info "Testing application health..."
    local frontend_url=$(kubectl get ingress -n "$NAMESPACE" -o jsonpath='{.items[0].spec.rules[0].host}')
    
    if [[ -n "$frontend_url" ]]; then
        if curl -f "https://$frontend_url/health" > /dev/null 2>&1; then
            log_success "Frontend health check passed"
        else
            log_warning "Frontend health check failed"
        fi
    fi
    
    log_success "Health checks completed"
}

# Display deployment information
show_deployment_info() {
    log_step "Deployment Information"
    
    echo -e "${CYAN}=================================${NC}"
    echo -e "${CYAN}🎉 Deployment Completed Successfully!${NC}"
    echo -e "${CYAN}=================================${NC}"
    echo ""
    
    # Get ingress URL
    local ingress_url=$(kubectl get ingress -n "$NAMESPACE" -o jsonpath='{.items[0].spec.rules[0].host}')
    if [[ -n "$ingress_url" ]]; then
        echo -e "${GREEN}🌐 Application URL: https://$ingress_url${NC}"
    fi
    
    # Get load balancer IP
    local lb_ip=$(kubectl get service ai-absence-sow-lb -n "$NAMESPACE" -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
    if [[ -n "$lb_ip" ]]; then
        echo -e "${GREEN}🔗 Load Balancer IP: $lb_ip${NC}"
    fi
    
    echo ""
    echo -e "${BLUE}📊 Monitoring:${NC}"
    echo -e "  Grafana: kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80"
    echo -e "  Prometheus: kubectl port-forward -n monitoring svc/prometheus-kube-prometheus-prometheus 9090:9090"
    echo ""
    
    echo -e "${BLUE}🔧 Management Commands:${NC}"
    echo -e "  View pods: kubectl get pods -n $NAMESPACE"
    echo -e "  View logs: kubectl logs -f deployment/backend -n $NAMESPACE"
    echo -e "  Scale deployment: kubectl scale deployment backend --replicas=5 -n $NAMESPACE"
    echo ""
    
    echo -e "${BLUE}🔐 Secrets Management:${NC}"
    echo -e "  Update Gemini API key: kubectl patch secret app-secrets -n $NAMESPACE -p '{\"stringData\":{\"GEMINI_API_KEY\":\"new-key\"}}'"
    echo ""
}

# Main deployment function
main() {
    echo -e "${PURPLE}🚀 AI Absence & SOW System - Oracle Cloud Deployment${NC}"
    echo -e "${PURPLE}=================================================${NC}"
    echo ""
    
    # Parse command line arguments
    local skip_build=false
    local skip_infrastructure=false
    local skip_monitoring=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-build)
                skip_build=true
                shift
                ;;
            --skip-infrastructure)
                skip_infrastructure=true
                shift
                ;;
            --skip-monitoring)
                skip_monitoring=true
                shift
                ;;
            -h|--help)
                echo "Usage: $0 [OPTIONS]"
                echo "Options:"
                echo "  --skip-build         Skip Docker image building"
                echo "  --skip-infrastructure Skip Terraform infrastructure deployment"
                echo "  --skip-monitoring    Skip monitoring stack installation"
                echo "  -h, --help          Show this help message"
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done
    
    # Run deployment steps
    check_prerequisites
    
    if [[ "$skip_build" != true ]]; then
        build_images
        push_images
    fi
    
    if [[ "$skip_infrastructure" != true ]]; then
        deploy_infrastructure
    fi
    
    deploy_kubernetes
    configure_ssl
    
    if [[ "$skip_monitoring" != true ]]; then
        install_monitoring
    fi
    
    health_checks
    show_deployment_info
    
    log_success "Deployment completed successfully! 🎉"
}

# Run main function
main "$@"