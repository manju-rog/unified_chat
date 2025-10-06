#!/bin/bash

# 🔧 Comprehensive Troubleshooting Script
# Diagnoses and fixes common deployment issues

set -e

# Configuration
NAMESPACE="ai-absence-sow"
LOG_DIR="troubleshooting-logs"

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

log_debug() {
    echo -e "${BLUE}[DEBUG]${NC} $1"
}

# Create log directory
mkdir -p "$LOG_DIR"

# Check cluster connectivity
check_cluster_connectivity() {
    log_debug "Checking cluster connectivity..."
    
    if kubectl cluster-info &> "$LOG_DIR/cluster-info.log"; then
        log_info "✅ Cluster connectivity OK"
        kubectl cluster-info >> "$LOG_DIR/cluster-info.log"
    else
        log_error "❌ Cannot connect to cluster"
        cat "$LOG_DIR/cluster-info.log"
        return 1
    fi
}

# Check namespace status
check_namespace() {
    log_debug "Checking namespace status..."
    
    if kubectl get namespace $NAMESPACE &> "$LOG_DIR/namespace.log"; then
        log_info "✅ Namespace $NAMESPACE exists"
    else
        log_error "❌ Namespace $NAMESPACE not found"
        log_info "Creating namespace..."
        kubectl create namespace $NAMESPACE
        log_info "✅ Namespace created"
    fi
}

# Check pod status and diagnose issues
diagnose_pods() {
    log_debug "Diagnosing pod issues..."
    
    # Get all pods in namespace
    kubectl get pods -n $NAMESPACE -o wide > "$LOG_DIR/pods-status.log"
    
    # Check for failed pods
    local failed_pods=$(kubectl get pods -n $NAMESPACE --field-selector=status.phase=Failed -o name 2>/dev/null)
    local pending_pods=$(kubectl get pods -n $NAMESPACE --field-selector=status.phase=Pending -o name 2>/dev/null)
    
    if [[ -n "$failed_pods" ]]; then
        log_error "❌ Found failed pods:"
        echo "$failed_pods"
        
        # Get logs from failed pods
        for pod in $failed_pods; do
            local pod_name=$(echo $pod | cut -d'/' -f2)
            log_info "Getting logs for failed pod: $pod_name"
            kubectl logs -n $NAMESPACE $pod_name --previous > "$LOG_DIR/failed-pod-$pod_name.log" 2>&1 || true
            kubectl describe pod -n $NAMESPACE $pod_name > "$LOG_DIR/failed-pod-$pod_name-describe.log" 2>&1
        done
    fi
    
    if [[ -n "$pending_pods" ]]; then
        log_warn "⚠️ Found pending pods:"
        echo "$pending_pods"
        
        # Describe pending pods to find issues
        for pod in $pending_pods; do
            local pod_name=$(echo $pod | cut -d'/' -f2)
            log_info "Describing pending pod: $pod_name"
            kubectl describe pod -n $NAMESPACE $pod_name > "$LOG_DIR/pending-pod-$pod_name-describe.log" 2>&1
            
            # Check for common issues
            if grep -q "Insufficient cpu" "$LOG_DIR/pending-pod-$pod_name-describe.log"; then
                log_error "❌ Pod $pod_name: Insufficient CPU resources"
            fi
            if grep -q "Insufficient memory" "$LOG_DIR/pending-pod-$pod_name-describe.log"; then
                log_error "❌ Pod $pod_name: Insufficient memory resources"
            fi
            if grep -q "no nodes available" "$LOG_DIR/pending-pod-$pod_name-describe.log"; then
                log_error "❌ Pod $pod_name: No nodes available for scheduling"
            fi
        done
    fi
    
    # Check running pods for issues
    local running_pods=$(kubectl get pods -n $NAMESPACE --field-selector=status.phase=Running -o name 2>/dev/null)
    for pod in $running_pods; do
        local pod_name=$(echo $pod | cut -d'/' -f2)
        
        # Check if pod is ready
        local ready=$(kubectl get pod -n $NAMESPACE $pod_name -o jsonpath='{.status.containerStatuses[0].ready}' 2>/dev/null)
        if [[ "$ready" != "true" ]]; then
            log_warn "⚠️ Pod $pod_name is running but not ready"
            kubectl describe pod -n $NAMESPACE $pod_name > "$LOG_DIR/not-ready-pod-$pod_name-describe.log" 2>&1
        fi
        
        # Check for restart loops
        local restarts=$(kubectl get pod -n $NAMESPACE $pod_name -o jsonpath='{.status.containerStatuses[0].restartCount}' 2>/dev/null)
        if [[ "$restarts" -gt 5 ]]; then
            log_error "❌ Pod $pod_name has high restart count: $restarts"
            kubectl logs -n $NAMESPACE $pod_name --tail=100 > "$LOG_DIR/high-restart-pod-$pod_name.log" 2>&1
        fi
    done
}

# Check service endpoints
check_services() {
    log_debug "Checking service endpoints..."
    
    kubectl get services -n $NAMESPACE > "$LOG_DIR/services.log"
    kubectl get endpoints -n $NAMESPACE > "$LOG_DIR/endpoints.log"
    
    # Check if services have endpoints
    local services=$(kubectl get services -n $NAMESPACE -o name 2>/dev/null)
    for service in $services; do
        local service_name=$(echo $service | cut -d'/' -f2)
        local endpoints=$(kubectl get endpoints -n $NAMESPACE $service_name -o jsonpath='{.subsets[*].addresses[*].ip}' 2>/dev/null | wc -w)
        
        if [[ $endpoints -eq 0 ]]; then
            log_error "❌ Service $service_name has no endpoints"
            kubectl describe service -n $NAMESPACE $service_name > "$LOG_DIR/no-endpoints-service-$service_name.log" 2>&1
        else
            log_info "✅ Service $service_name has $endpoints endpoint(s)"
        fi
    done
}

# Check ingress configuration
check_ingress() {
    log_debug "Checking ingress configuration..."
    
    if kubectl get ingress -n $NAMESPACE &> "$LOG_DIR/ingress.log"; then
        local ingress_name=$(kubectl get ingress -n $NAMESPACE -o name | head -1 | cut -d'/' -f2)
        
        if [[ -n "$ingress_name" ]]; then
            kubectl describe ingress -n $NAMESPACE $ingress_name > "$LOG_DIR/ingress-describe.log" 2>&1
            
            # Check if ingress has external IP
            local external_ip=$(kubectl get ingress -n $NAMESPACE $ingress_name -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null)
            if [[ -z "$external_ip" ]]; then
                log_warn "⚠️ Ingress $ingress_name has no external IP"
            else
                log_info "✅ Ingress $ingress_name has external IP: $external_ip"
            fi
        fi
    else
        log_warn "⚠️ No ingress found in namespace"
    fi
}

# Check persistent volumes
check_storage() {
    log_debug "Checking storage configuration..."
    
    kubectl get pv > "$LOG_DIR/persistent-volumes.log" 2>&1
    kubectl get pvc -n $NAMESPACE > "$LOG_DIR/persistent-volume-claims.log" 2>&1
    
    # Check PVC status
    local pvcs=$(kubectl get pvc -n $NAMESPACE -o name 2>/dev/null)
    for pvc in $pvcs; do
        local pvc_name=$(echo $pvc | cut -d'/' -f2)
        local status=$(kubectl get pvc -n $NAMESPACE $pvc_name -o jsonpath='{.status.phase}' 2>/dev/null)
        
        if [[ "$status" != "Bound" ]]; then
            log_error "❌ PVC $pvc_name is not bound (Status: $status)"
            kubectl describe pvc -n $NAMESPACE $pvc_name > "$LOG_DIR/unbound-pvc-$pvc_name.log" 2>&1
        else
            log_info "✅ PVC $pvc_name is bound"
        fi
    done
}

# Check database connectivity
check_database() {
    log_debug "Checking database connectivity..."
    
    local db_pod=$(kubectl get pods -n $NAMESPACE -l app=postgres -o name | head -1 | cut -d'/' -f2)
    
    if [[ -n "$db_pod" ]]; then
        # Check if database is ready
        if kubectl exec -n $NAMESPACE $db_pod -- pg_isready -q 2>/dev/null; then
            log_info "✅ Database is ready"
        else
            log_error "❌ Database is not ready"
            kubectl logs -n $NAMESPACE $db_pod --tail=50 > "$LOG_DIR/database-logs.log" 2>&1
        fi
        
        # Test database connection
        if kubectl exec -n $NAMESPACE $db_pod -- psql -U postgres -d ai_absence_db -c "SELECT 1;" &>/dev/null; then
            log_info "✅ Database connection successful"
        else
            log_error "❌ Database connection failed"
            kubectl exec -n $NAMESPACE $db_pod -- psql -U postgres -l > "$LOG_DIR/database-list.log" 2>&1 || true
        fi
    else
        log_error "❌ Database pod not found"
    fi
}

# Check resource usage
check_resources() {
    log_debug "Checking resource usage..."
    
    # Node resources
    kubectl top nodes > "$LOG_DIR/node-resources.log" 2>&1 || log_warn "Metrics server not available"
    
    # Pod resources
    kubectl top pods -n $NAMESPACE > "$LOG_DIR/pod-resources.log" 2>&1 || log_warn "Pod metrics not available"
    
    # Check for resource constraints
    kubectl describe nodes > "$LOG_DIR/node-describe.log" 2>&1
    
    # Check for evicted pods
    local evicted_pods=$(kubectl get pods -n $NAMESPACE --field-selector=status.phase=Failed -o jsonpath='{.items[?(@.status.reason=="Evicted")].metadata.name}' 2>/dev/null)
    if [[ -n "$evicted_pods" ]]; then
        log_error "❌ Found evicted pods: $evicted_pods"
        for pod in $evicted_pods; do
            kubectl describe pod -n $NAMESPACE $pod > "$LOG_DIR/evicted-pod-$pod.log" 2>&1
        done
    fi
}

# Check network connectivity
check_network() {
    log_debug "Checking network connectivity..."
    
    # Test internal service connectivity
    local test_pod="network-test-$(date +%s)"
    
    # Create a test pod
    kubectl run $test_pod -n $NAMESPACE --image=busybox --rm -it --restart=Never -- /bin/sh -c "
        echo 'Testing internal connectivity...'
        nslookup backend-service.$NAMESPACE.svc.cluster.local
        nslookup frontend-service.$NAMESPACE.svc.cluster.local
        nslookup absence-service.$NAMESPACE.svc.cluster.local
        nslookup postgres-service.$NAMESPACE.svc.cluster.local
    " > "$LOG_DIR/network-test.log" 2>&1 &
    
    # Wait for test to complete
    sleep 30
    
    # Check network policies
    kubectl get networkpolicies -n $NAMESPACE > "$LOG_DIR/network-policies.log" 2>&1
}

# Auto-fix common issues
auto_fix_issues() {
    log_debug "Attempting to auto-fix common issues..."
    
    # Restart failed deployments
    local failed_deployments=$(kubectl get deployments -n $NAMESPACE -o jsonpath='{.items[?(@.status.readyReplicas==0)].metadata.name}' 2>/dev/null)
    for deployment in $failed_deployments; do
        log_info "Restarting failed deployment: $deployment"
        kubectl rollout restart deployment/$deployment -n $NAMESPACE
    done
    
    # Clean up evicted pods
    local evicted_pods=$(kubectl get pods -n $NAMESPACE --field-selector=status.phase=Failed -o name 2>/dev/null)
    for pod in $evicted_pods; do
        log_info "Cleaning up evicted pod: $pod"
        kubectl delete $pod -n $NAMESPACE --ignore-not-found=true
    done
    
    # Restart pods with high restart count
    local high_restart_pods=$(kubectl get pods -n $NAMESPACE -o jsonpath='{.items[?(@.status.containerStatuses[0].restartCount>10)].metadata.name}' 2>/dev/null)
    for pod in $high_restart_pods; do
        log_info "Restarting pod with high restart count: $pod"
        kubectl delete pod -n $NAMESPACE $pod --ignore-not-found=true
    done
}

# Generate troubleshooting report
generate_report() {
    log_debug "Generating troubleshooting report..."
    
    local report_file="$LOG_DIR/troubleshooting-report-$(date +%Y%m%d_%H%M%S).md"
    
    cat > "$report_file" << EOF
# 🔧 Troubleshooting Report

**Generated**: $(date)
**Namespace**: $NAMESPACE
**Cluster**: $(kubectl config current-context)

## Cluster Status

### Nodes
\`\`\`
$(kubectl get nodes 2>/dev/null || echo "Unable to get nodes")
\`\`\`

### Pods Status
\`\`\`
$(cat "$LOG_DIR/pods-status.log" 2>/dev/null || echo "No pod status available")
\`\`\`

### Services Status
\`\`\`
$(cat "$LOG_DIR/services.log" 2>/dev/null || echo "No service status available")
\`\`\`

### Storage Status
\`\`\`
$(cat "$LOG_DIR/persistent-volume-claims.log" 2>/dev/null || echo "No PVC status available")
\`\`\`

## Issues Found

$(if ls "$LOG_DIR"/failed-pod-*.log 1> /dev/null 2>&1; then
    echo "### Failed Pods"
    for log in "$LOG_DIR"/failed-pod-*.log; do
        echo "#### $(basename "$log" .log)"
        echo "\`\`\`"
        tail -20 "$log"
        echo "\`\`\`"
    done
fi)

$(if ls "$LOG_DIR"/pending-pod-*-describe.log 1> /dev/null 2>&1; then
    echo "### Pending Pods"
    for log in "$LOG_DIR"/pending-pod-*-describe.log; do
        echo "#### $(basename "$log" -describe.log)"
        echo "\`\`\`"
        grep -A 5 -B 5 "Events:" "$log" || echo "No events found"
        echo "\`\`\`"
    done
fi)

## Recommendations

1. **Check Resource Limits**: Ensure pods have appropriate CPU and memory limits
2. **Verify Image Pull**: Check if container images are accessible
3. **Database Connectivity**: Ensure database is running and accessible
4. **Network Policies**: Verify network policies allow required traffic
5. **Storage**: Check if persistent volumes are properly bound

## Next Steps

1. Review the detailed logs in the $LOG_DIR directory
2. Check application-specific logs for errors
3. Verify configuration files and secrets
4. Consider scaling resources if needed
5. Monitor system after applying fixes

EOF

    log_info "Troubleshooting report generated: $report_file"
}

# Main troubleshooting function
main() {
    log_info "🔧 Starting Comprehensive Troubleshooting"
    log_info "========================================="
    
    # Run all diagnostic checks
    check_cluster_connectivity
    check_namespace
    diagnose_pods
    check_services
    check_ingress
    check_storage
    check_database
    check_resources
    check_network
    
    # Attempt auto-fixes
    auto_fix_issues
    
    # Generate report
    generate_report
    
    log_info "========================================="
    log_info "🎉 Troubleshooting completed!"
    log_info "Logs and report available in $LOG_DIR/"
}

# Run troubleshooting
main "$@"