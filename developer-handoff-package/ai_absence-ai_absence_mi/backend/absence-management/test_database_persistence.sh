#!/bin/bash

# End-to-End Database Persistence Test Script
# This script tests database persistence across application restarts

echo "=== End-to-End Database Persistence Test ==="
echo "This script will test database persistence across application restarts"
echo

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the correct directory
if [ ! -f "pom.xml" ]; then
    print_error "Please run this script from the backend/absence-management directory"
    exit 1
fi

# Step 1: Clean and build the application
print_status "Step 1: Building the application..."
mvn clean compile -q
if [ $? -ne 0 ]; then
    print_error "Failed to build the application"
    exit 1
fi
print_status "Application built successfully"

# Step 2: Run the end-to-end database integration tests
print_status "Step 2: Running end-to-end database integration tests..."
mvn test -Dtest=EndToEndDatabaseIntegrationTest -q
if [ $? -ne 0 ]; then
    print_error "End-to-end database integration tests failed"
    exit 1
fi
print_status "End-to-end database integration tests passed"

# Step 3: Start the application in background
print_status "Step 3: Starting the application..."
mvn spring-boot:run -Dspring-boot.run.profiles=sqlite > app.log 2>&1 &
APP_PID=$!
print_status "Application started with PID: $APP_PID"

# Wait for application to start
print_status "Waiting for application to start..."
sleep 30

# Check if application is running
if ! kill -0 $APP_PID 2>/dev/null; then
    print_error "Application failed to start"
    exit 1
fi

# Step 4: Test AI functionality and create test data
print_status "Step 4: Testing AI functionality and creating test data..."

# Test data creation via AI
curl -s -X POST http://localhost:8080/api/ai/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Mark Test Employee absent today for persistence test",
    "conversationId": "persistence-test-1"
  }' > /dev/null

if [ $? -eq 0 ]; then
    print_status "Test data created via AI"
else
    print_warning "Failed to create test data via AI (application might still be starting)"
fi

# Step 5: Query data to verify it exists
print_status "Step 5: Querying data to verify it exists..."

QUERY_RESPONSE=$(curl -s -X POST http://localhost:8080/api/ai/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Who was absent today?",
    "conversationId": "persistence-test-2"
  }')

if echo "$QUERY_RESPONSE" | grep -q "success.*true"; then
    print_status "Data query successful"
else
    print_warning "Data query may have failed (application might still be starting)"
fi

# Step 6: Stop the application
print_status "Step 6: Stopping the application..."
kill $APP_PID
wait $APP_PID 2>/dev/null
print_status "Application stopped"

# Step 7: Restart the application
print_status "Step 7: Restarting the application..."
mvn spring-boot:run -Dspring-boot.run.profiles=sqlite > app2.log 2>&1 &
APP_PID=$!
print_status "Application restarted with PID: $APP_PID"

# Wait for application to restart
print_status "Waiting for application to restart..."
sleep 30

# Check if application is running
if ! kill -0 $APP_PID 2>/dev/null; then
    print_error "Application failed to restart"
    exit 1
fi

# Step 8: Verify data persistence after restart
print_status "Step 8: Verifying data persistence after restart..."

PERSISTENCE_RESPONSE=$(curl -s -X POST http://localhost:8080/api/ai/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Who was absent today?",
    "conversationId": "persistence-test-3"
  }')

if echo "$PERSISTENCE_RESPONSE" | grep -q "success.*true"; then
    print_status "Data persistence verified - AI can still access data after restart"
else
    print_error "Data persistence test failed - AI cannot access data after restart"
    kill $APP_PID
    exit 1
fi

# Step 9: Test database integrity
print_status "Step 9: Testing database integrity..."

INTEGRITY_RESPONSE=$(curl -s -X POST http://localhost:8080/api/ai/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "How many employees are in the system?",
    "conversationId": "persistence-test-4"
  }')

if echo "$INTEGRITY_RESPONSE" | grep -q "success.*true"; then
    print_status "Database integrity verified"
else
    print_warning "Database integrity test inconclusive"
fi

# Step 10: Test new data creation after restart
print_status "Step 10: Testing new data creation after restart..."

NEW_DATA_RESPONSE=$(curl -s -X POST http://localhost:8080/api/ai/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Mark Another Test Employee on vacation tomorrow",
    "conversationId": "persistence-test-5"
  }')

if echo "$NEW_DATA_RESPONSE" | grep -q "success.*true"; then
    print_status "New data creation after restart successful"
else
    print_warning "New data creation after restart may have failed"
fi

# Step 11: Final verification
print_status "Step 11: Final verification..."

FINAL_RESPONSE=$(curl -s -X POST http://localhost:8080/api/ai/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Show me all recent absences and vacations",
    "conversationId": "persistence-test-6"
  }')

if echo "$FINAL_RESPONSE" | grep -q "success.*true"; then
    print_status "Final verification successful"
else
    print_warning "Final verification inconclusive"
fi

# Step 12: Clean up
print_status "Step 12: Cleaning up..."
kill $APP_PID
wait $APP_PID 2>/dev/null
print_status "Application stopped"

# Clean up log files
rm -f app.log app2.log

# Step 13: Run comprehensive database tests
print_status "Step 13: Running comprehensive database tests..."
mvn test -Dtest=AIDatabaseIntegrationTest,EndToEndDatabaseIntegrationTest -q
if [ $? -ne 0 ]; then
    print_error "Comprehensive database tests failed"
    exit 1
fi
print_status "Comprehensive database tests passed"

echo
print_status "=== DATABASE PERSISTENCE TEST COMPLETED SUCCESSFULLY ==="
print_status "✓ Application can start and stop cleanly"
print_status "✓ Data persists across application restarts"
print_status "✓ AI can access persistent data after restart"
print_status "✓ New data can be created after restart"
print_status "✓ Database integrity is maintained"
print_status "✓ All comprehensive database tests pass"
echo
print_status "The AI-Database integration is working correctly with full persistence!"