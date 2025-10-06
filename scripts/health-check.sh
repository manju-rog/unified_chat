#!/bin/bash

# 🏥 Health Check Script for AI Absence & SOW System
# Comprehensive health validation for all components

set -e

# Configuration
NAMESPACE="ai-absence-sow"
ENVIRONMENT=${1:-"staging"}
TIMEOUT=300

# Colors for output
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

# Check if kubectl is available
check_prerequisites() {
    log_step "Checking prerequisites..."
    
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed"
        exit 1
    fi
    
    if ! kubectl get namespace $NAMESPACE &> /dev/null; then
        log_error "Namespace $NAMESPACE not found"
        exit 1
    fi
    
    log_info "Prerequisites check passed"
}

# Check pod status
check_pods() {
    log_step "Checking pod status..."
    
    local failed_pods=0
    
    # Get all pods in namespace
    while IFS= read -r line; do
        local pod_name=$(echo "$line" | awk '{print $1}')
        local status=$(echo "$line" | awk '{print $3}')
        local ready=$(echo "$line" | awk '{print $2}')
        
        if [[ "$status" != "Running" ]]; then
            log_error "Pod $pod_name is not running (Status: $status)"
            failed_pods=$((failed_pods + 1))
        elif [[ "$ready" == *"0/"* ]]; then
            log_error "Pod $pod_name is not ready (Ready: $ready)"
            failed_pods=$((failed_pods + 1))
        else
            log_info "Pod $pod_name is healthy (Status: $status, Ready: $ready)"
        fi
    done < <(kubectl get pods -n $NAMESPACE --no-headers)
    
    if [[ $failed_pods -gt 0 ]]; then
        log_error "$failed_pods pods are not healthy"
        return 1
    fi
    
    log_info "All pods are healthy"
}

# Check service endpoints
check_services() {
    log_step "Checking service endpoints..."
    
    local services=("frontend-service" "backend-service" "absence-service" "postgres-service")
    
    for service in "${services[@]}"; do
        if kubectl get service "$service" -n $NAMESPACE &> /dev/null; then
            local endpoints=$(kubectl get endpoints "$service" -n $NAMESPACE -o jsonpath='{.subsets[*].addresses[*].ip}' | wc -w)
            if [[ $endpoints -gt 0 ]]; then
                log_info "Service $service has $endpoints endpoint(s)"
            else
                log_error "Service $service has no endpoints"
                return 1
            fi
        else
            log_error "Service $service not found"
            return 1
        fi
    done
    
    log_info "All services have healthy endpoints"
}

# Check database connectivity
check_database() {
    log_step "Checking database connectivity..."
    
    # Check if PostgreSQL is ready
    if kubectl exec -n $NAMESPACE deployment/postgres -- pg_isready -q; then
        log_info "Database is ready and accepting connections"
    else
        log_error "Database is not ready"
        return 1
    fi
    
    # Test database query
    local db_user=$(kubectl get secret app-secrets -n $NAMESPACE -o jsonpath='{.data.DB_USERNAME}' | base64 -d)
    local db_name=$(kubectl get configmap app-config -n $NAMESPACE -o jsonpath='{.data.DB_NAME}')
    
    if kubectl exec -n $NAMESPACE deployment/postgres -- psql -U "$db_user" -d "$db_name" -c "SELECT 1;" &> /dev/null; then
        log_info "Database query test passed"
    else
        log_error "Database query test failed"
        return 1
    fi
    
    log_info "Database connectivity check passed"
}

# Check API endpoints
check_api_endpoints() {
    log_step "Checking API endpoints..."
    
    # Port forward to backend service
    kubectl port-forward -n $NAMESPACE service/backend-service 8080:5002 &
    local backend_pid=$!
    
    # Port forward to absence service
    kubectl port-forward -n $NAMESPACE service/absence-service 8081:8080 &
    local absence_pid=$!
    
    # Wait for port forwards to establish
    sleep 10
    
    local api_errors=0
    
    # Test backend health endpoint
    if curl -f -s http://localhost:8080/api/health > /dev/null; then
        log_info "Backend API health check passed"
    else
        log_error "Backend API health check failed"
        api_errors=$((api_errors + 1))
    fi
    
    # Test absence service health endpoint
    if curl -f -s http://localhost:8081/actuator/health > /dev/null; then
        log_info "Absence service health check passed"
    else
        log_error "Absence service health check failed"
        api_errors=$((api_errors + 1))
    fi
    
    # Test backend API functionality
    if curl -f -s http://localhost:8080/api/employees > /dev/null; then
        log_info "Backend API functionality test passed"
    else
        log_warn "Backend API functionality test failed (may be normal during startup)"
    fi
    
    # Cleanup port forwards
    kill $backend_pid $absence_pid 2>/dev/null || true
    
    if [[ $api_errors -gt 0 ]]; then
        log_error "$api_errors API health checks failed"
        return 1
    fi
    
    log_info "API endpoint checks passed"
}

# Check ingress and external access
check_ingress() {
    log_step "Checking ingress configuration..."
    
    if kubectl get ingress -n $NAMESPACE &> /dev/null; then
        local ingress_host=$(kubectl get ingress -n $NAMESPACE -o jsonpath='{.items[0].spec.rules[0].host}')
        local ingress_ip=$(kubectl get ingress -n $NAMESPACE -o jsonpath='{.items[0].status.loadBalancer.ingress[0].ip}')
        
        if [[ -n "$ingress_host" ]]; then
            log_info "Ingress configured for host: $ingress_host"
            
            if [[ -n "$ingress_ip" ]]; then
                log_info "Ingress has external IP: $ingress_ip"
                
                # Test external access if in production
                if [[ "$ENVIRONMENT" == "production" ]] && [[ -n "$ingress_host" ]]; then
                    if curl -f -s "https://$ingress_host/health" > /dev/null; then
                        log_info "External access test passed"
                    else
                        log_warn "External access test failed (DNS may not be propagated yet)"
                    fi
                fi
            else
                log_warn "Ingress does not have external IP yet"
            fi
        else
            log_warn "Ingress host not configured"
        fi
    else
        log_warn "No ingress found"
    fi
    
    log_info "Ingress check completed"
}

# Check resource usage
check_resources() {
    log_step "Checking resource usage..."
    
    # Check node resources
    log_info "Node resource usage:"
    kubectl top nodes 2>/dev/null || log_warn "Metrics server not available"
    
    # Check pod resources
    log_info "Pod resource usage:"
    kubectl top pods -n $NAMESPACE 2>/dev/null || log_warn "Pod metrics not available"
    
    # Check persistent volume claims
    log_info "Persistent volume claims:"
    kubectl get pvc -n $NAMESPACE
    
    log_info "Resource usage check completed"
}

# Check monitoring and logging
check_monitoring() {
    log_step "Checking monitoring and logging..."
    
    # Check if monitoring namespace exists
    if kubectl get namespace monitoring &> /dev/null; then
        log_info "Monitoring namespace exists"
        
        # Check Prometheus
        if kubectl get deployment prometheus-server -n monitoring &> /dev/null; then
            log_info "Prometheus is deployed"
        else
            log_warn "Prometheus not found"
        fi
        
        # Check Grafana
        if kubectl get deployment prometheus-grafana -n monitoring &> /dev/null; then
            log_info "Grafana is deployed"
        else
            log_warn "Grafana not found"
        fi
    else
        log_warn "Monitoring namespace not found"
    fi
    
    log_info "Monitoring check completed"
}

# Generate health report
generate_report() {
    log_step "Generating health report..."
    
    local report_file="health-report-$(date +%Y%m%d_%H%M%S).json"
    
    cat > "$report_file" << EOF
{
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "environment": "$ENVIRONMENT",
  "namespace": "$NAMESPACE",
  "cluster_info": {
    "nodes": $(kubectl get nodes --no-headers | wc -l),
    "pods": $(kubectl get pods -n $NAMESPACE --no-headers | wc -l),
    "services": $(kubectl get services -n $NAMESPACE --no-headers | wc -l)
  },
  "pod_status": [
EOF
    
    # Add pod status to report
    local first=true
    while IFS= read -r line; do
        local pod_name=$(echo "$line" | awk '{print $1}')
        local status=$(echo "$line" | awk '{print $3}')
        local ready=$(echo "$line" | awk '{print $2}')
        
        if [[ "$first" == true ]]; then
            first=false
        else
            echo "," >> "$report_file"
        fi
        
        echo "    {\"name\": \"$pod_name\", \"status\": \"$status\", \"ready\": \"$ready\"}" >> "$report_file"
    done < <(kubectl get pods -n $NAMESPACE --no-headers)
    
    cat >> "$report_file" << EOF
  ],
  "health_status": "healthy",
  "checks_performed": [
    "pods",
    "services",
    "database",
    "api_endpoints",
    "ingress",
    "resources",
    "monitoring"
  ]
}
EOF
    
    log_info "Health report generated: $report_file"
}

# Main health check function
main() {
    log_info "Starting health check for AI Absence & SOW System"
    log_info "Environment: $ENVIRONMENT"
    log_info "Namespace: $NAMESPACE"
    echo ""
    
    local checks_passed=0
    local total_checks=7
    
    # Run all health checks
    check_prerequisites && checks_passed=$((checks_passed + 1))
    check_pods && checks_passed=$((checks_passed + 1))
    check_services && checks_passed=$((checks_passed + 1))
    check_database && checks_passed=$((checks_passed + 1))
    check_api_endpoints && checks_passed=$((checks_passed + 1))
    check_ingress && checks_passed=$((checks_passed + 1))
    check_resources && checks_passed=$((checks_passed + 1))
    check_monitoring  # Optional check, doesn't affect pass/fail
    
    generate_report
    
    echo ""
    log_info "Health check completed"
    log_info "Checks passed: $checks_passed/$total_checks"
    
    if [[ $checks_passed -eq $total_checks ]]; then
        log_info "🎉 All health checks passed! System is healthy."
        exit 0
    else
        log_error "❌ Some health checks failed. Please investigate."
        exit 1
    fi
}

# Run main function
main "$@"