#!/bin/bash

# 💾 Backup Script for AI Absence & SOW System
# Automated backup of database and persistent volumes

set -e

# Configuration
NAMESPACE="ai-absence-sow"
BACKUP_DIR="/backups/ai-absence-sow"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=7

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
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

# Create backup directory
create_backup_dir() {
    log_info "Creating backup directory: $BACKUP_DIR/$DATE"
    mkdir -p "$BACKUP_DIR/$DATE"
}

# Backup PostgreSQL database
backup_database() {
    log_info "Starting database backup..."
    
    # Get database credentials
    DB_USER=$(kubectl get secret app-secrets -n $NAMESPACE -o jsonpath='{.data.DB_USERNAME}' | base64 -d)
    DB_PASSWORD=$(kubectl get secret app-secrets -n $NAMESPACE -o jsonpath='{.data.DB_PASSWORD}' | base64 -d)
    DB_NAME=$(kubectl get configmap app-config -n $NAMESPACE -o jsonpath='{.data.DB_NAME}')
    
    # Create database dump
    kubectl exec -n $NAMESPACE deployment/postgres -- pg_dump \
        -U "$DB_USER" \
        -d "$DB_NAME" \
        --no-password \
        --verbose \
        --clean \
        --if-exists \
        --create > "$BACKUP_DIR/$DATE/database_backup.sql"
    
    # Compress the backup
    gzip "$BACKUP_DIR/$DATE/database_backup.sql"
    
    log_info "Database backup completed: database_backup.sql.gz"
}

# Backup persistent volumes
backup_volumes() {
    log_info "Starting persistent volume backup..."
    
    # Backup generated documents
    kubectl exec -n $NAMESPACE deployment/backend -- tar -czf - /app/generated_docs | \
        cat > "$BACKUP_DIR/$DATE/generated_docs_backup.tar.gz"
    
    # Backup absence service data
    kubectl exec -n $NAMESPACE deployment/absence-service -- tar -czf - /app/data | \
        cat > "$BACKUP_DIR/$DATE/absence_data_backup.tar.gz"
    
    log_info "Persistent volume backup completed"
}

# Backup Kubernetes configurations
backup_k8s_configs() {
    log_info "Starting Kubernetes configuration backup..."
    
    # Create k8s backup directory
    mkdir -p "$BACKUP_DIR/$DATE/k8s-configs"
    
    # Backup all resources in namespace
    kubectl get all -n $NAMESPACE -o yaml > "$BACKUP_DIR/$DATE/k8s-configs/all-resources.yaml"
    kubectl get configmaps -n $NAMESPACE -o yaml > "$BACKUP_DIR/$DATE/k8s-configs/configmaps.yaml"
    kubectl get secrets -n $NAMESPACE -o yaml > "$BACKUP_DIR/$DATE/k8s-configs/secrets.yaml"
    kubectl get pvc -n $NAMESPACE -o yaml > "$BACKUP_DIR/$DATE/k8s-configs/persistent-volume-claims.yaml"
    kubectl get ingress -n $NAMESPACE -o yaml > "$BACKUP_DIR/$DATE/k8s-configs/ingress.yaml"
    
    # Compress k8s configs
    tar -czf "$BACKUP_DIR/$DATE/k8s_configs_backup.tar.gz" -C "$BACKUP_DIR/$DATE" k8s-configs
    rm -rf "$BACKUP_DIR/$DATE/k8s-configs"
    
    log_info "Kubernetes configuration backup completed"
}

# Create backup manifest
create_manifest() {
    log_info "Creating backup manifest..."
    
    cat > "$BACKUP_DIR/$DATE/backup_manifest.json" << EOF
{
  "backup_date": "$DATE",
  "backup_type": "full",
  "namespace": "$NAMESPACE",
  "files": [
    {
      "name": "database_backup.sql.gz",
      "type": "database",
      "size": "$(du -h "$BACKUP_DIR/$DATE/database_backup.sql.gz" | cut -f1)"
    },
    {
      "name": "generated_docs_backup.tar.gz",
      "type": "volume",
      "size": "$(du -h "$BACKUP_DIR/$DATE/generated_docs_backup.tar.gz" | cut -f1)"
    },
    {
      "name": "absence_data_backup.tar.gz",
      "type": "volume",
      "size": "$(du -h "$BACKUP_DIR/$DATE/absence_data_backup.tar.gz" | cut -f1)"
    },
    {
      "name": "k8s_configs_backup.tar.gz",
      "type": "configuration",
      "size": "$(du -h "$BACKUP_DIR/$DATE/k8s_configs_backup.tar.gz" | cut -f1)"
    }
  ],
  "total_size": "$(du -sh "$BACKUP_DIR/$DATE" | cut -f1)",
  "kubernetes_version": "$(kubectl version --short --client | grep 'Client Version')",
  "cluster_info": {
    "nodes": $(kubectl get nodes --no-headers | wc -l),
    "pods": $(kubectl get pods -n $NAMESPACE --no-headers | wc -l)
  }
}
EOF
    
    log_info "Backup manifest created"
}

# Cleanup old backups
cleanup_old_backups() {
    log_info "Cleaning up backups older than $RETENTION_DAYS days..."
    
    find "$BACKUP_DIR" -type d -name "20*" -mtime +$RETENTION_DAYS -exec rm -rf {} \; 2>/dev/null || true
    
    log_info "Cleanup completed"
}

# Verify backup integrity
verify_backup() {
    log_info "Verifying backup integrity..."
    
    # Check if all expected files exist
    local files=("database_backup.sql.gz" "generated_docs_backup.tar.gz" "absence_data_backup.tar.gz" "k8s_configs_backup.tar.gz" "backup_manifest.json")
    
    for file in "${files[@]}"; do
        if [[ ! -f "$BACKUP_DIR/$DATE/$file" ]]; then
            log_error "Backup file missing: $file"
            exit 1
        fi
    done
    
    # Test gzip files
    if ! gzip -t "$BACKUP_DIR/$DATE/database_backup.sql.gz"; then
        log_error "Database backup file is corrupted"
        exit 1
    fi
    
    # Test tar files
    for tar_file in generated_docs_backup.tar.gz absence_data_backup.tar.gz k8s_configs_backup.tar.gz; do
        if ! tar -tzf "$BACKUP_DIR/$DATE/$tar_file" > /dev/null; then
            log_error "Backup file is corrupted: $tar_file"
            exit 1
        fi
    done
    
    log_info "Backup integrity verification passed"
}

# Upload to Oracle Cloud Storage (optional)
upload_to_cloud() {
    if [[ -n "${OCI_BUCKET_NAME:-}" ]]; then
        log_info "Uploading backup to Oracle Cloud Storage..."
        
        # Create archive of entire backup
        tar -czf "$BACKUP_DIR/ai-absence-sow-backup-$DATE.tar.gz" -C "$BACKUP_DIR" "$DATE"
        
        # Upload using OCI CLI
        oci os object put \
            --bucket-name "$OCI_BUCKET_NAME" \
            --file "$BACKUP_DIR/ai-absence-sow-backup-$DATE.tar.gz" \
            --name "backups/ai-absence-sow-backup-$DATE.tar.gz"
        
        # Cleanup local archive
        rm "$BACKUP_DIR/ai-absence-sow-backup-$DATE.tar.gz"
        
        log_info "Backup uploaded to cloud storage"
    else
        log_warn "OCI_BUCKET_NAME not set, skipping cloud upload"
    fi
}

# Main backup function
main() {
    log_info "Starting AI Absence & SOW System backup - $DATE"
    
    # Check prerequisites
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed"
        exit 1
    fi
    
    if ! kubectl get namespace $NAMESPACE &> /dev/null; then
        log_error "Namespace $NAMESPACE not found"
        exit 1
    fi
    
    # Execute backup steps
    create_backup_dir
    backup_database
    backup_volumes
    backup_k8s_configs
    create_manifest
    verify_backup
    cleanup_old_backups
    upload_to_cloud
    
    log_info "Backup completed successfully!"
    log_info "Backup location: $BACKUP_DIR/$DATE"
    log_info "Total backup size: $(du -sh "$BACKUP_DIR/$DATE" | cut -f1)"
}

# Run main function
main "$@"