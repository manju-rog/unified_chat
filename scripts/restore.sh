#!/bin/bash

# 🔄 Restore Script for AI Absence & SOW System
# Restore database and persistent volumes from backup

set -e

# Configuration
NAMESPACE="ai-absence-sow"
BACKUP_DIR="/backups/ai-absence-sow"

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

# Show usage
show_usage() {
    echo "Usage: $0 <backup_date>"
    echo "Example: $0 20241006_143022"
    echo ""
    echo "Available backups:"
    ls -la "$BACKUP_DIR" | grep "^d" | grep "20" | awk '{print $9}' | sort -r | head -10
}

# Validate backup directory
validate_backup() {
    local backup_date=$1
    local backup_path="$BACKUP_DIR/$backup_date"
    
    if [[ ! -d "$backup_path" ]]; then
        log_error "Backup directory not found: $backup_path"
        exit 1
    fi
    
    # Check required files
    local required_files=("database_backup.sql.gz" "backup_manifest.json")
    for file in "${required_files[@]}"; do
        if [[ ! -f "$backup_path/$file" ]]; then
            log_error "Required backup file missing: $file"
            exit 1
        fi
    done
    
    log_info "Backup validation passed"
}

# Show backup information
show_backup_info() {
    local backup_date=$1
    local backup_path="$BACKUP_DIR/$backup_date"
    
    log_step "Backup Information"
    echo "================================"
    
    if [[ -f "$backup_path/backup_manifest.json" ]]; then
        echo "Backup Date: $(jq -r '.backup_date' "$backup_path/backup_manifest.json")"
        echo "Backup Type: $(jq -r '.backup_type' "$backup_path/backup_manifest.json")"
        echo "Total Size: $(jq -r '.total_size' "$backup_path/backup_manifest.json")"
        echo "Files:"
        jq -r '.files[] | "  - \(.name) (\(.type)): \(.size)"' "$backup_path/backup_manifest.json"
    else
        echo "Backup Date: $backup_date"
        echo "Size: $(du -sh "$backup_path" | cut -f1)"
    fi
    
    echo "================================"
}

# Confirm restore operation
confirm_restore() {
    log_warn "This operation will REPLACE all current data!"
    log_warn "Current database and volumes will be overwritten."
    echo ""
    read -p "Are you sure you want to continue? (yes/no): " confirm
    
    if [[ "$confirm" != "yes" ]]; then
        log_info "Restore operation cancelled"
        exit 0
    fi
}

# Scale down applications
scale_down_apps() {
    log_step "Scaling down applications..."
    
    kubectl scale deployment backend --replicas=0 -n $NAMESPACE
    kubectl scale deployment absence-service --replicas=0 -n $NAMESPACE
    kubectl scale deployment frontend --replicas=0 -n $NAMESPACE
    
    # Wait for pods to terminate
    log_info "Waiting for pods to terminate..."
    kubectl wait --for=delete pod -l app.kubernetes.io/name=ai-absence-sow -n $NAMESPACE --timeout=300s
    
    log_info "Applications scaled down"
}

# Restore database
restore_database() {
    local backup_date=$1
    local backup_path="$BACKUP_DIR/$backup_date"
    
    log_step "Restoring database..."
    
    # Get database credentials
    DB_USER=$(kubectl get secret app-secrets -n $NAMESPACE -o jsonpath='{.data.DB_USERNAME}' | base64 -d)
    DB_PASSWORD=$(kubectl get secret app-secrets -n $NAMESPACE -o jsonpath='{.data.DB_PASSWORD}' | base64 -d)
    DB_NAME=$(kubectl get configmap app-config -n $NAMESPACE -o jsonpath='{.data.DB_NAME}')
    
    # Restore database from backup
    gunzip -c "$backup_path/database_backup.sql.gz" | \
        kubectl exec -i -n $NAMESPACE deployment/postgres -- psql -U "$DB_USER" -d "$DB_NAME"
    
    log_info "Database restore completed"
}

# Restore persistent volumes
restore_volumes() {
    local backup_date=$1
    local backup_path="$BACKUP_DIR/$backup_date"
    
    log_step "Restoring persistent volumes..."
    
    # Restore generated documents
    if [[ -f "$backup_path/generated_docs_backup.tar.gz" ]]; then
        log_info "Restoring generated documents..."
        kubectl exec -n $NAMESPACE deployment/backend -- rm -rf /app/generated_docs/*
        cat "$backup_path/generated_docs_backup.tar.gz" | \
            kubectl exec -i -n $NAMESPACE deployment/backend -- tar -xzf - -C /
    fi
    
    # Restore absence service data
    if [[ -f "$backup_path/absence_data_backup.tar.gz" ]]; then
        log_info "Restoring absence service data..."
        kubectl exec -n $NAMESPACE deployment/absence-service -- rm -rf /app/data/*
        cat "$backup_path/absence_data_backup.tar.gz" | \
            kubectl exec -i -n $NAMESPACE deployment/absence-service -- tar -xzf - -C /
    fi
    
    log_info "Persistent volumes restore completed"
}

# Scale up applications
scale_up_apps() {
    log_step "Scaling up applications..."
    
    # Scale up database first
    kubectl scale statefulset postgres --replicas=1 -n $NAMESPACE
    kubectl wait --for=condition=ready pod -l app.kubernetes.io/component=database -n $NAMESPACE --timeout=300s
    
    # Scale up absence service
    kubectl scale deployment absence-service --replicas=2 -n $NAMESPACE
    kubectl wait --for=condition=available deployment/absence-service -n $NAMESPACE --timeout=300s
    
    # Scale up backend
    kubectl scale deployment backend --replicas=3 -n $NAMESPACE
    kubectl wait --for=condition=available deployment/backend -n $NAMESPACE --timeout=300s
    
    # Scale up frontend
    kubectl scale deployment frontend --replicas=2 -n $NAMESPACE
    kubectl wait --for=condition=available deployment/frontend -n $NAMESPACE --timeout=300s
    
    log_info "Applications scaled up"
}

# Verify restore
verify_restore() {
    log_step "Verifying restore..."
    
    # Check database connectivity
    if kubectl exec -n $NAMESPACE deployment/postgres -- pg_isready -q; then
        log_info "Database is ready"
    else
        log_error "Database is not ready"
        exit 1
    fi
    
    # Check application health
    local services=("backend-service" "absence-service" "frontend-service")
    for service in "${services[@]}"; do
        if kubectl get service "$service" -n $NAMESPACE &> /dev/null; then
            log_info "Service $service is available"
        else
            log_error "Service $service is not available"
            exit 1
        fi
    done
    
    # Test API endpoints
    log_info "Testing API endpoints..."
    kubectl port-forward -n $NAMESPACE service/backend-service 8080:5002 &
    local port_forward_pid=$!
    
    sleep 5
    
    if curl -f http://localhost:8080/api/health &> /dev/null; then
        log_info "Backend API is responding"
    else
        log_warn "Backend API is not responding (this may be normal during startup)"
    fi
    
    kill $port_forward_pid 2>/dev/null || true
    
    log_info "Restore verification completed"
}

# Create restore log
create_restore_log() {
    local backup_date=$1
    local restore_date=$(date +%Y%m%d_%H%M%S)
    
    cat > "$BACKUP_DIR/restore_log_$restore_date.json" << EOF
{
  "restore_date": "$restore_date",
  "backup_date": "$backup_date",
  "namespace": "$NAMESPACE",
  "restored_by": "$(whoami)",
  "kubernetes_version": "$(kubectl version --short --client | grep 'Client Version')",
  "cluster_info": {
    "nodes": $(kubectl get nodes --no-headers | wc -l),
    "pods": $(kubectl get pods -n $NAMESPACE --no-headers | wc -l)
  },
  "status": "completed"
}
EOF
    
    log_info "Restore log created: restore_log_$restore_date.json"
}

# Main restore function
main() {
    if [[ $# -ne 1 ]]; then
        show_usage
        exit 1
    fi
    
    local backup_date=$1
    
    log_info "Starting AI Absence & SOW System restore"
    log_info "Backup date: $backup_date"
    
    # Check prerequisites
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed"
        exit 1
    fi
    
    if ! kubectl get namespace $NAMESPACE &> /dev/null; then
        log_error "Namespace $NAMESPACE not found"
        exit 1
    fi
    
    # Validate backup
    validate_backup "$backup_date"
    
    # Show backup information
    show_backup_info "$backup_date"
    
    # Confirm restore
    confirm_restore
    
    # Execute restore steps
    scale_down_apps
    restore_database "$backup_date"
    restore_volumes "$backup_date"
    scale_up_apps
    verify_restore
    create_restore_log "$backup_date"
    
    log_info "Restore completed successfully!"
    log_info "All services should be available in a few minutes"
}

# Run main function
main "$@"