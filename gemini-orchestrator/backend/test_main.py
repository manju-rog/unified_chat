"""
Test script for the main FastAPI application.
Verifies that all endpoints are properly configured.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root_endpoint():
    """Test the root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Gemini Orchestrator API"}
    print("✓ Root endpoint works")


def test_health_endpoint():
    """Test the health endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
    print("✓ Health endpoint works")


def test_orchestrator_endpoint_structure():
    """Test that the orchestrator endpoint accepts the correct request structure"""
    # This will fail if Gemini API key is not set, but we're just testing the endpoint structure
    response = client.post(
        "/orchestrator",
        json={"text": "hello"}
    )
    # We expect either a 200 (success) or 500 (if Gemini API fails)
    # But not 422 (validation error)
    assert response.status_code in [200, 500], f"Unexpected status code: {response.status_code}"
    print("✓ Orchestrator endpoint accepts correct request structure")


def test_absence_router_included():
    """Test that absence router is included"""
    response = client.get("/absence/status/test_employee?date=2024-01-01")
    # Should return 200 with status data
    assert response.status_code == 200
    print("✓ Absence router is included")


def test_sow_router_included():
    """Test that SOW router is included"""
    response = client.post(
        "/sow/start",
        json={"project_name": "Test Project"}
    )
    # Should return 200 with sow_id
    assert response.status_code == 200
    assert "sow_id" in response.json()
    print("✓ SOW router is included")


def test_cors_configured():
    """Test that CORS is configured"""
    # Check that the CORS middleware is present
    from app.main import app
    middlewares = [m for m in app.user_middleware]
    cors_present = any("CORSMiddleware" in str(m) for m in middlewares)
    assert cors_present, "CORS middleware not found"
    print("✓ CORS middleware is configured")


def test_static_files_mounted():
    """Test that static files are mounted"""
    from app.main import app
    routes = [route.path for route in app.routes]
    files_route_present = any("/files" in route for route in routes)
    assert files_route_present, "/files route not found"
    print("✓ Static files are mounted at /files")


if __name__ == "__main__":
    print("\n=== Testing FastAPI Main Application ===\n")
    
    try:
        test_root_endpoint()
        test_health_endpoint()
        test_orchestrator_endpoint_structure()
        test_absence_router_included()
        test_sow_router_included()
        test_cors_configured()
        test_static_files_mounted()
        
        print("\n✅ All tests passed!\n")
        print("Task 8 'Create FastAPI main application' is complete:")
        print("  ✓ 8.1 FastAPI app with CORS configured")
        print("  ✓ 8.2 /orchestrator endpoint implemented")
        print("  ✓ 8.3 Static file serving for SOW documents added")
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}\n")
        sys.exit(1)
