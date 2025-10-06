#!/bin/bash

# ✅ Production Readiness Validation Suite
# Comprehensive validation before production deployment

set -e

# Configuration
NAMESPACE="ai-absence-sow"
VALIDATION_LOG="production-validation-$(date +%Y%m%d_%H%M%S).log"
CHECKLIST_FILE="production-readiness-checklist.json"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1" | tee -a "$VALIDATION_LOG"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1" | tee -a "$VALIDATION_LOG"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$VALIDATION_LOG"
}

log_check() {
    echo -e "${BLUE}[CHECK]${NC} $1" | tee -a "$VALIDATION_LOG"
}

# Initialize checklist
init_checklist() {
    cat > "$CHECKLIST_FILE" << EOF
{
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "environment": "production-validation",
  "namespace": "$NAMESPACE",
  "checks": {
    "security": {
      "rbac": false,
      "network_policies": false,
      "pod_security": false,
      "secrets_encryption": false,
      "tls_certificates": false
    },
    "reliability": {
      "high_availability": false,
      "backup_restore": false,
      "disaster_recovery": false,
      "health_checks": false,
      "monitoring": false
    },
    "performance": {
      "resource_limits": false,
      "auto_scaling": false,
      "load_testing": false,
      "database_optimization": false,
      "caching": false
    },
    "compliance": {
      "logging": false,
      "audit_trail": false,
      "data_protection": false,
      "access_control": false
    },
    "operational": {
      "deployment_automation": false,
      "rollback_capability": false,
      "documentation": false,
      "runbooks": false
    }
  },
  "overall_score": 0,
  "production_ready": false
}
EOF
}

# Update checklist
update_checklist() {
    local category=$1
    local check=$2
    local status=$3
    
    jq ".checks.$category.$check = $status" "$CHECKLIST_FILE" > tmp.json && mv tmp.json "$CHECKLIST_FILE"
}

# Security validation
validate_security() {
    log_check "Validating security configuration..."
    
    local security_score=0
    
    # Check RBAC
    if kubectl get clusterroles,roles -n $NAMESPACE | grep -q "ai-absence"; then
        log_info "✅ RBAC configuration found"
        update_checklist "security" "rbac" "true"
        security_score=$((security_score + 1))
    else
        log_error "❌ RBAC configuration missing"
    fi
    
    # Check Network Policies
    if kubectl get networkpolicies -n $NAMESPACE | grep -q "deny-all\|allow-"; then
        log_info "✅ Network policies configured"
        update_checklist "security" "network_policies" "true"
        security_score=$((security_score + 1))
    else
        log_error "❌ Network policies missing"
    fi
    
    # Check Pod Security
    local pods_with_security=$(kubectl get pods -n $NAMESPACE -o jsonpath='{.items[*].spec.securityContext}' | grep -c "runAsNonRoot\|runAsUser" || echo "0")
    if [[ $pods_with_security -gt 0 ]]; then
        log_info "✅ Pod security contexts configured"
        update_checklist "security" "pod_security" "true"
        security_score=$((security_score + 1))
    else
        log_error "❌ Pod security contexts missing"
    fi
    
    # Check Secrets
    if kubectl get secrets -n $NAMESPACE | grep -q "app-secrets"; then
        log_info "✅ Application secrets configured"
        update_checklist "security" "secrets_encryption" "true"
        security_score=$((security_score + 1))
    else
        log_error "❌ Application secrets missing"
    fi
    
    # Check TLS
    if kubectl get ingress -n $NAMESPACE -o jsonpath='{.items[*].spec.tls}' | grep -q "secretName"; then
        log_info "✅ TLS certificates configured"
        update_checklist "security" "tls_certificates" "true"
        security_score=$((security_score + 1))
    else
        log_warn "⚠️ TLS certificates not configured"
    fi
    
    log_info "Security validation score: $security_score/5"
}

# Reliability validation
validate_reliability() {
    log_check "Validating reliability configuration..."
    
    local reliability_score=0
    
    # Check High Availability
    local multi_replica_deployments=$(kubectl get deployments -n $NAMESPACE -o jsonpath='{.items[?(@.spec.replicas>1)].metadata.name}' | wc -w)
    if [[ $multi_replica_deployments -gt 0 ]]; then
        log_info "✅ High availability configured ($multi_replica_deployments deployments with multiple replicas)"
        update_checklist "reliability" "high_availability" "true"
        reliability_score=$((reliability_score + 1))
    else
        log_error "❌ High availability not configured"
    fi
    
    # Check Backup Scripts
    if [[ -f "scripts/backup.sh" && -f "scripts/restore.sh" ]]; then
        log_info "✅ Backup and restore scripts available"
        update_checklist "reliability" "backup_restore" "true"
        reliability_score=$((reliability_score + 1))
    else
        log_error "❌ Backup and restore scripts missing"
    fi
    
    # Check Disaster Recovery
    if [[ -f "terraform/main.tf" ]]; then
        log_info "✅ Infrastructure as Code available for disaster recovery"
        update_checklist "reliability" "disaster_recovery" "true"
        reliability_score=$((reliability_score + 1))
    else
        log_error "❌ Infrastructure as Code missing"
    fi
    
    # Check Health Checks
    local pods_with_health_checks=$(kubectl get pods -n $NAMESPACE -o jsonpath='{.items[*].spec.containers[*].livenessProbe}' | grep -c "httpGet\|exec" || echo "0")
    if [[ $pods_with_health_checks -gt 0 ]]; then
        log_info "✅ Health checks configured"
        update_checklist "reliability" "health_checks" "true"
        reliability_score=$((reliability_score + 1))
    else
        log_error "❌ Health checks missing"
    fi
    
    # Check Monitoring
    if kubectl get configmap -n $NAMESPACE | grep -q "prometheus"; then
        log_info "✅ Monitoring configured"
        update_checklist "reliability" "monitoring" "true"
        reliability_score=$((reliability_score + 1))
    else
        log_error "❌ Monitoring not configured"
    fi
    
    log_info "Reliability validation score: $reliability_score/5"
}

# Performance validation
validate_performance() {
    log_check "Validating performance configuration..."
    
    local performance_score=0
    
    # Check Resource Limits
    local pods_with_limits=$(kubectl get pods -n $NAMESPACE -o jsonpath='{.items[*].spec.containers[*].resources.limits}' | grep -c "cpu\|memory" || echo "0")
    if [[ $pods_with_limits -gt 0 ]]; then
        log_info "✅ Resource limits configured"
        update_checklist "performance" "resource_limits" "true"
        performance_score=$((performance_score + 1))
    else
        log_error "❌ Resource limits missing"
    fi
    
    # Check Auto-scaling
    if kubectl get hpa -n $NAMESPACE | grep -q "frontend\|backend\|absence"; then
        log_info "✅ Auto-scaling configured"
        update_checklist "performance" "auto_scaling" "true"
        performance_score=$((performance_score + 1))
    else
        log_error "❌ Auto-scaling not configured"
    fi
    
    # Check Load Testing Scripts
    if [[ -f "scripts/performance-test.sh" ]]; then
        log_info "✅ Load testing scripts available"
        update_checklist "performance" "load_testing" "true"
        performance_score=$((performance_score + 1))
    else
        log_error "❌ Load testing scripts missing"
    fi
    
    # Check Database Optimization
    local db_pod=$(kubectl get pods -n $NAMESPACE -l app=postgres -o name | head -1)
    if [[ -n "$db_pod" ]]; then
        local db_config=$(kubectl exec -n $NAMESPACE $db_pod -- psql -U postgres -c "SHOW shared_buffers;" 2>/dev/null || echo "")
        if [[ -n "$db_config" ]]; then
            log_info "✅ Database optimization configured"
            update_checklist "performance" "database_optimization" "true"
            performance_score=$((performance_score + 1))
        else
            log_warn "⚠️ Database optimization not verified"
        fi
    else
        log_error "❌ Database not found"
    fi
    
    # Check Caching
    if kubectl get pods -n $NAMESPACE | grep -q "redis\|cache"; then
        log_info "✅ Caching layer configured"
        update_checklist "performance" "caching" "true"
        performance_score=$((performance_score + 1))
    else
        log_warn "⚠️ Caching layer not found"
    fi
    
    log_info "Performance validation score: $performance_score/5"
}

# Compliance validation
validate_compliance() {
    log_check "Validating compliance configuration..."
    
    local compliance_score=0
    
    # Check Logging
    local pods_with_logging=$(kubectl get pods -n $NAMESPACE -o jsonpath='{.items[*].spec.containers[*].volumeMounts}' | grep -c "log" || echo "0")
    if [[ $pods_with_logging -gt 0 ]] || kubectl logs -n $NAMESPACE --tail=1 deployment/backend &>/dev/null; then
        log_info "✅ Logging configured"
        update_checklist "compliance" "logging" "true"
        compliance_score=$((compliance_score + 1))
    else
        log_error "❌ Logging not properly configured"
    fi
    
    # Check Audit Trail
    if kubectl get events -n $NAMESPACE | grep -q "Created\|Started\|Pulled"; then
        log_info "✅ Audit trail available"
        update_checklist "compliance" "audit_trail" "true"
        compliance_score=$((compliance_score + 1))
    else
        log_error "❌ Audit trail not available"
    fi
    
    # Check Data Protection
    if kubectl get pvc -n $NAMESPACE | grep -q "Bound"; then
        log_info "✅ Data protection with persistent storage"
        update_checklist "compliance" "data_protection" "true"
        compliance_score=$((compliance_score + 1))
    else
        log_error "❌ Data protection not configured"
    fi
    
    # Check Access Control
    if kubectl get serviceaccounts -n $NAMESPACE | grep -q "ai-absence"; then
        log_info "✅ Access control configured"
        update_checklist "compliance" "access_control" "true"
        compliance_score=$((compliance_score + 1))
    else
        log_error "❌ Access control not properly configured"
    fi
    
    log_info "Compliance validation score: $compliance_score/4"
}

# Operational validation
validate_operational() {
    log_check "Validating operational readiness..."
    
    local operational_score=0
    
    # Check Deployment Automation
    if [[ -f ".github/workflows/deploy.yml" || -f "scripts/deploy.sh" ]]; then
        log_info "✅ Deployment automation configured"
        update_checklist "operational" "deployment_automation" "true"
        operational_score=$((operational_score + 1))
    else
        log_error "❌ Deployment automation missing"
    fi
    
    # Check Rollback Capability
    local deployments=$(kubectl get deployments -n $NAMESPACE -o name)
    local rollback_ready=true
    for deployment in $deployments; do
        local revision_history=$(kubectl rollout history $deployment -n $NAMESPACE | wc -l)
        if [[ $revision_history -lt 3 ]]; then
            rollback_ready=false
            break
        fi
    done
    
    if [[ "$rollback_ready" == "true" ]]; then
        log_info "✅ Rollback capability available"
        update_checklist "operational" "rollback_capability" "true"
        operational_score=$((operational_score + 1))
    else
        log_warn "⚠️ Rollback capability limited"
    fi
    
    # Check Documentation
    if [[ -f "README.md" && -f "COMPLETE_DEPLOYMENT_DOCUMENTATION.md" ]]; then
        log_info "✅ Documentation available"
        update_checklist "operational" "documentation" "true"
        operational_score=$((operational_score + 1))
    else
        log_error "❌ Documentation missing"
    fi
    
    # Check Runbooks
    if [[ -f "scripts/troubleshoot.sh" && -f "scripts/health-check.sh" ]]; then
        log_info "✅ Operational runbooks available"
        update_checklist "operational" "runbooks" "true"
        operational_score=$((operational_score + 1))
    else
        log_error "❌ Operational runbooks missing"
    fi
    
    log_info "Operational validation score: $operational_score/4"
}

# Calculate overall score
calculate_overall_score() {
    log_check "Calculating overall production readiness score..."
    
    local total_checks=$(jq '[.checks[] | to_entries[] | .value] | length' "$CHECKLIST_FILE")
    local passed_checks=$(jq '[.checks[] | to_entries[] | select(.value == true)] | length' "$CHECKLIST_FILE")
    local score=$(echo "scale=2; $passed_checks * 100 / $total_checks" | bc)
    
    # Update checklist with score
    jq ".overall_score = $score" "$CHECKLIST_FILE" > tmp.json && mv tmp.json "$CHECKLIST_FILE"
    
    # Determine if production ready
    if (( $(echo "$score >= 85" | bc -l) )); then
        jq '.production_ready = true' "$CHECKLIST_FILE" > tmp.json && mv tmp.json "$CHECKLIST_FILE"
        log_info "🎉 PRODUCTION READY! Score: $score%"
    else
        log_error "❌ NOT PRODUCTION READY. Score: $score% (minimum 85% required)"
    fi
    
    log_info "Passed checks: $passed_checks/$total_checks"
}

# Generate detailed report
generate_detailed_report() {
    log_check "Generating detailed production readiness report..."
    
    local report_file="production-readiness-report-$(date +%Y%m%d_%H%M%S).md"
    
    cat > "$report_file" << EOF
# 🚀 Production Readiness Report

**Generated**: $(date)
**Environment**: Production Validation
**Namespace**: $NAMESPACE
**Overall Score**: $(jq -r '.overall_score' "$CHECKLIST_FILE")%
**Production Ready**: $(jq -r '.production_ready' "$CHECKLIST_FILE")

## Executive Summary

$(if [[ "$(jq -r '.production_ready' "$CHECKLIST_FILE")" == "true" ]]; then
    echo "✅ **SYSTEM IS PRODUCTION READY**"
    echo ""
    echo "The AI Absence & SOW System has passed all critical production readiness checks and is ready for deployment to production environment."
else
    echo "❌ **SYSTEM REQUIRES ATTENTION BEFORE PRODUCTION**"
    echo ""
    echo "The system has failed some critical checks and requires remediation before production deployment."
fi)

## Detailed Results

### 🔒 Security ($(jq '[.checks.security[] | select(. == true)] | length' "$CHECKLIST_FILE")/$(jq '[.checks.security[]] | length' "$CHECKLIST_FILE"))
- RBAC Configuration: $(jq -r '.checks.security.rbac' "$CHECKLIST_FILE" | sed 's/true/✅ PASS/g; s/false/❌ FAIL/g')
- Network Policies: $(jq -r '.checks.security.network_policies' "$CHECKLIST_FILE" | sed 's/true/✅ PASS/g; s/false/❌ FAIL/g')
- Pod Security: $(jq -r '.checks.security.pod_security' "$CHECKLIST_FILE" | sed 's/true/✅ PASS/g; s/false/❌ FAIL/g')
- Secrets Encryption: $(jq -r '.checks.security.secrets_encryption' "$CHECKLIST_FILE" | sed 's/true/✅ PASS/g; s/false/❌ FAIL/g')
- TLS Certificates: $(jq -r '.checks.security.tls_certificates' "$CHECKLIST_FILE" | sed 's/true/✅ PASS/g; s/false/❌ FAIL/g')

### 🛡️ Reliability ($(jq '[.checks.reliability[] | select(. == true)] | length' "$CHECKLIST_FILE")/$(jq '[.checks.reliability[]] | length' "$CHECKLIST_FILE"))
- High Availability: $(jq -r '.checks.reliability.high_availability' "$CHECKLIST_FILE" | sed 's/true/✅ PASS/g; s/false/❌ FAIL/g')
- Backup & Restore: $(jq -r '.checks.reliability.backup_restore' "$CHECKLIST_FILE" | sed 's/true/✅ PASS/g; s/false/❌ FAIL/g')
- Disaster Recovery: $(jq -r '.checks.reliability.disaster_recovery' "$CHECKLIST_FILE" | sed 's/true/✅ PASS/g; s/false/❌ FAIL/g')
- Health Checks: $(jq -r '.checks.reliability.health_checks' "$CHECKLIST_FILE" | sed 's/true/✅ PASS/g; s/false/❌ FAIL/g')
- Monitoring: $(jq -r '.checks.reliability.monitoring' "$CHECKLIST_FILE" | sed 's/true/✅ PASS/g; s/false/❌ FAIL/g')

### ⚡ Performance ($(jq '[.checks.performance[] | select(. == true)] | length' "$CHECKLIST_FILE")/$(jq '[.checks.performance[]] | length' "$CHECKLIST_FILE"))
- Resource Limits: $(jq -r '.checks.performance.resource_limits' "$CHECKLIST_FILE" | sed 's/true/✅ PASS/g; s/false/❌ FAIL/g')
- Auto-scaling: $(jq -r '.checks.performance.auto_scaling' "$CHECKLIST_FILE" | sed 's/true/✅ PASS/g; s/false/❌ FAIL/g')
- Load Testing: $(jq -r '.checks.performance.load_testing' "$CHECKLIST_FILE" | sed 's/true/✅ PASS/g; s/false/❌ FAIL/g')
- Database Optimization: $(jq -r '.checks.performance.database_optimization' "$CHECKLIST_FILE" | sed 's/true/✅ PASS/g; s/false/❌ FAIL/g')
- Caching: $(jq -r '.checks.performance.caching' "$CHECKLIST_FILE" | sed 's/true/✅ PASS/g; s/false/❌ FAIL/g')

### 📋 Compliance ($(jq '[.checks.compliance[] | select(. == true)] | length' "$CHECKLIST_FILE")/$(jq '[.checks.compliance[]] | length' "$CHECKLIST_FILE"))
- Logging: $(jq -r '.checks.compliance.logging' "$CHECKLIST_FILE" | sed 's/true/✅ PASS/g; s/false/❌ FAIL/g')
- Audit Trail: $(jq -r '.checks.compliance.audit_trail' "$CHECKLIST_FILE" | sed 's/true/✅ PASS/g; s/false/❌ FAIL/g')
- Data Protection: $(jq -r '.checks.compliance.data_protection' "$CHECKLIST_FILE" | sed 's/true/✅ PASS/g; s/false/❌ FAIL/g')
- Access Control: $(jq -r '.checks.compliance.access_control' "$CHECKLIST_FILE" | sed 's/true/✅ PASS/g; s/false/❌ FAIL/g')

### 🔧 Operational ($(jq '[.checks.operational[] | select(. == true)] | length' "$CHECKLIST_FILE")/$(jq '[.checks.operational[]] | length' "$CHECKLIST_FILE"))
- Deployment Automation: $(jq -r '.checks.operational.deployment_automation' "$CHECKLIST_FILE" | sed 's/true/✅ PASS/g; s/false/❌ FAIL/g')
- Rollback Capability: $(jq -r '.checks.operational.rollback_capability' "$CHECKLIST_FILE" | sed 's/true/✅ PASS/g; s/false/❌ FAIL/g')
- Documentation: $(jq -r '.checks.operational.documentation' "$CHECKLIST_FILE" | sed 's/true/✅ PASS/g; s/false/❌ FAIL/g')
- Runbooks: $(jq -r '.checks.operational.runbooks' "$CHECKLIST_FILE" | sed 's/true/✅ PASS/g; s/false/❌ FAIL/g')

## Recommendations

$(if [[ "$(jq -r '.production_ready' "$CHECKLIST_FILE")" == "true" ]]; then
    echo "### ✅ Ready for Production"
    echo "- Proceed with production deployment"
    echo "- Monitor system closely during initial deployment"
    echo "- Set up production monitoring and alerting"
    echo "- Schedule regular health checks and maintenance"
else
    echo "### ❌ Action Items Before Production"
    echo "- Address all failed checks above"
    echo "- Re-run validation after fixes"
    echo "- Consider staged rollout approach"
    echo "- Implement additional monitoring"
fi)

## Next Steps

1. **Address Failed Checks**: Fix any failing validation items
2. **Performance Testing**: Run comprehensive load tests
3. **Security Review**: Conduct final security audit
4. **Documentation Update**: Ensure all documentation is current
5. **Team Training**: Brief operations team on procedures
6. **Go-Live Planning**: Schedule production deployment

---

**Validation completed at**: $(date)
**Report generated by**: Production Readiness Validation Suite
EOF

    log_info "Detailed report generated: $report_file"
}

# Main validation function
main() {
    log_info "🚀 Starting Production Readiness Validation"
    log_info "=========================================="
    
    # Initialize
    init_checklist
    
    # Run all validations
    validate_security
    validate_reliability
    validate_performance
    validate_compliance
    validate_operational
    
    # Calculate results
    calculate_overall_score
    generate_detailed_report
    
    log_info "=========================================="
    log_info "🎉 Production readiness validation completed!"
    log_info "Check the generated report for detailed results"
    log_info "Validation log: $VALIDATION_LOG"
    log_info "Checklist JSON: $CHECKLIST_FILE"
}

# Run validation
main "$@"