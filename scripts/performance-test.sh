#!/bin/bash

# 🚀 Performance Testing Suite
# Load testing and performance validation

set -e

# Configuration
NAMESPACE="ai-absence-sow"
FRONTEND_URL="http://localhost:3000"
BACKEND_URL="http://localhost:5002"
ABSENCE_URL="http://localhost:8080"

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

log_test() {
    echo -e "${BLUE}[PERF]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_test "Checking performance testing prerequisites..."
    
    # Check if kubectl is available
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed"
        exit 1
    fi
    
    # Check if curl is available
    if ! command -v curl &> /dev/null; then
        log_error "curl is not installed"
        exit 1
    fi
    
    # Check if ab (Apache Bench) is available
    if ! command -v ab &> /dev/null; then
        log_warn "Apache Bench (ab) not found. Installing..."
        if command -v brew &> /dev/null; then
            brew install httpd
        elif command -v apt-get &> /dev/null; then
            sudo apt-get update && sudo apt-get install -y apache2-utils
        else
            log_error "Cannot install Apache Bench. Please install manually."
            exit 1
        fi
    fi
    
    log_info "Prerequisites check completed"
}

# Setup port forwarding
setup_port_forwarding() {
    log_test "Setting up port forwarding for testing..."
    
    # Kill existing port forwards
    pkill -f "kubectl port-forward" || true
    sleep 2
    
    # Frontend port forward
    kubectl port-forward -n $NAMESPACE service/frontend-service 3000:80 &
    FRONTEND_PID=$!
    
    # Backend port forward
    kubectl port-forward -n $NAMESPACE service/backend-service 5002:5002 &
    BACKEND_PID=$!
    
    # Absence service port forward
    kubectl port-forward -n $NAMESPACE service/absence-service 8080:8080 &
    ABSENCE_PID=$!
    
    # Wait for port forwards to establish
    sleep 10
    
    log_info "Port forwarding established"
}

# Cleanup port forwarding
cleanup_port_forwarding() {
    log_info "Cleaning up port forwarding..."
    kill $FRONTEND_PID $BACKEND_PID $ABSENCE_PID 2>/dev/null || true
}

# Test API response times
test_api_response_times() {
    log_test "Testing API response times..."
    
    # Test backend health endpoint
    log_info "Testing backend health endpoint..."
    local backend_time=$(curl -o /dev/null -s -w '%{time_total}' $BACKEND_URL/api/health)
    log_info "Backend health response time: ${backend_time}s"
    
    # Test absence service health endpoint
    log_info "Testing absence service health endpoint..."
    local absence_time=$(curl -o /dev/null -s -w '%{time_total}' $ABSENCE_URL/actuator/health)
    log_info "Absence service health response time: ${absence_time}s"
    
    # Test frontend
    log_info "Testing frontend response time..."
    local frontend_time=$(curl -o /dev/null -s -w '%{time_total}' $FRONTEND_URL)
    log_info "Frontend response time: ${frontend_time}s"
    
    # Validate response times
    if (( $(echo "$backend_time < 2.0" | bc -l) )); then
        log_info "✅ Backend response time acceptable"
    else
        log_warn "⚠️ Backend response time high: ${backend_time}s"
    fi
    
    if (( $(echo "$absence_time < 2.0" | bc -l) )); then
        log_info "✅ Absence service response time acceptable"
    else
        log_warn "⚠️ Absence service response time high: ${absence_time}s"
    fi
}

# Load testing with Apache Bench
run_load_tests() {
    log_test "Running load tests with Apache Bench..."
    
    # Create results directory
    mkdir -p performance-results
    
    # Test backend API
    log_info "Load testing backend API..."
    ab -n 1000 -c 10 -g performance-results/backend-load.dat $BACKEND_URL/api/health > performance-results/backend-load.txt 2>&1
    
    # Test absence service API
    log_info "Load testing absence service API..."
    ab -n 1000 -c 10 -g performance-results/absence-load.dat $ABSENCE_URL/actuator/health > performance-results/absence-load.txt 2>&1
    
    # Test frontend
    log_info "Load testing frontend..."
    ab -n 500 -c 5 -g performance-results/frontend-load.dat $FRONTEND_URL/ > performance-results/frontend-load.txt 2>&1
    
    log_info "Load test results saved to performance-results/"
}

# Stress testing
run_stress_tests() {
    log_test "Running stress tests..."
    
    # High concurrency test
    log_info "Running high concurrency test..."
    ab -n 5000 -c 50 -t 60 $BACKEND_URL/api/health > performance-results/stress-test.txt 2>&1
    
    # Sustained load test
    log_info "Running sustained load test (5 minutes)..."
    ab -n 10000 -c 20 -t 300 $BACKEND_URL/api/health > performance-results/sustained-load.txt 2>&1
    
    log_info "Stress test results saved to performance-results/"
}

# Memory and CPU monitoring
monitor_resources() {
    log_test "Monitoring resource usage during tests..."
    
    # Monitor pods
    kubectl top pods -n $NAMESPACE > performance-results/pod-resources-before.txt
    
    # Run a quick load test while monitoring
    ab -n 2000 -c 20 $BACKEND_URL/api/health > /dev/null 2>&1 &
    LOAD_PID=$!
    
    # Monitor during load
    sleep 30
    kubectl top pods -n $NAMESPACE > performance-results/pod-resources-during.txt
    
    wait $LOAD_PID
    
    # Monitor after load
    sleep 10
    kubectl top pods -n $NAMESPACE > performance-results/pod-resources-after.txt
    
    log_info "Resource monitoring completed"
}

# Database performance test
test_database_performance() {
    log_test "Testing database performance..."
    
    # Test database connection time
    local db_pod=$(kubectl get pods -n $NAMESPACE -l app=postgres -o jsonpath='{.items[0].metadata.name}')
    
    if [[ -n "$db_pod" ]]; then
        log_info "Testing database connection..."
        local db_time=$(kubectl exec -n $NAMESPACE $db_pod -- time psql -U postgres -d ai_absence_db -c "SELECT 1;" 2>&1 | grep real | awk '{print $2}')
        log_info "Database query time: $db_time"
        
        # Test database under load
        log_info "Testing database under concurrent load..."
        for i in {1..10}; do
            kubectl exec -n $NAMESPACE $db_pod -- psql -U postgres -d ai_absence_db -c "SELECT COUNT(*) FROM information_schema.tables;" &
        done
        wait
        
        log_info "Database performance test completed"
    else
        log_warn "Database pod not found, skipping database performance test"
    fi
}

# Generate performance report
generate_performance_report() {
    log_test "Generating performance report..."
    
    local report_file="performance-results/performance-report-$(date +%Y%m%d_%H%M%S).md"
    
    cat > "$report_file" << EOF
# 📊 Performance Test Report

**Generated**: $(date)
**Environment**: Kubernetes Cluster
**Namespace**: $NAMESPACE

## Test Summary

### API Response Times
- Backend Health: $(grep "time_total" performance-results/backend-load.txt | head -1 || echo "N/A")
- Absence Service Health: $(grep "time_total" performance-results/absence-load.txt | head -1 || echo "N/A")
- Frontend: $(grep "time_total" performance-results/frontend-load.txt | head -1 || echo "N/A")

### Load Test Results

#### Backend API Load Test
\`\`\`
$(tail -10 performance-results/backend-load.txt 2>/dev/null || echo "No results available")
\`\`\`

#### Absence Service Load Test
\`\`\`
$(tail -10 performance-results/absence-load.txt 2>/dev/null || echo "No results available")
\`\`\`

#### Frontend Load Test
\`\`\`
$(tail -10 performance-results/frontend-load.txt 2>/dev/null || echo "No results available")
\`\`\`

### Resource Usage

#### Before Load Test
\`\`\`
$(cat performance-results/pod-resources-before.txt 2>/dev/null || echo "No data available")
\`\`\`

#### During Load Test
\`\`\`
$(cat performance-results/pod-resources-during.txt 2>/dev/null || echo "No data available")
\`\`\`

#### After Load Test
\`\`\`
$(cat performance-results/pod-resources-after.txt 2>/dev/null || echo "No data available")
\`\`\`

## Recommendations

1. **Response Times**: All APIs should respond within 2 seconds under normal load
2. **Throughput**: System should handle at least 100 requests/second per service
3. **Resource Usage**: CPU usage should stay below 80% under normal load
4. **Memory Usage**: Memory usage should stay below 85% under normal load

## Next Steps

- Monitor performance in production
- Set up automated performance testing in CI/CD
- Configure alerts for performance degradation
- Consider horizontal scaling if needed

EOF

    log_info "Performance report generated: $report_file"
}

# Main performance testing function
main() {
    log_info "🚀 Starting Performance Testing Suite"
    log_info "====================================="
    
    # Setup
    check_prerequisites
    setup_port_forwarding
    
    # Trap to cleanup on exit
    trap cleanup_port_forwarding EXIT
    
    # Run tests
    test_api_response_times
    run_load_tests
    run_stress_tests
    monitor_resources
    test_database_performance
    
    # Generate report
    generate_performance_report
    
    log_info "====================================="
    log_info "🎉 Performance testing completed!"
    log_info "Results available in performance-results/"
}

# Run performance tests
main "$@"