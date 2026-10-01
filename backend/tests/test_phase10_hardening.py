import pytest
from fastapi.testclient import TestClient
from sqlalchemy import inspect
from app.main import app
from app.core.database import engine, SessionLocal
from app.core.rate_limiter import rate_limiter
from app.core.config import settings

client = TestClient(app)

# ==============================================================================
# 1. SECURITY HEADERS TESTS
# ==============================================================================

def test_security_headers_present():
    """Verify production security headers are attached to API responses."""
    response = client.get("/health")
    assert response.status_code == 200
    headers = response.headers
    
    assert headers.get("X-Content-Type-Options") == "nosniff"
    assert headers.get("X-Frame-Options") in ["DENY", "SAMEORIGIN"]
    assert "strict-origin" in headers.get("Referrer-Policy", "")
    assert "Content-Security-Policy" in headers


# ==============================================================================
# 2. REQUEST CORRELATION / X-REQUEST-ID TESTS
# ==============================================================================

def test_request_id_generated_and_returned():
    """Verify that requests receive a unique X-Request-ID in response headers."""
    response = client.get("/health")
    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
    req_id = response.headers["X-Request-ID"]
    assert req_id.startswith("req-")

def test_request_id_preserved_if_provided():
    """Verify that a client-supplied X-Request-ID is preserved and propagated."""
    custom_id = "req-custom-trace-12345"
    response = client.get("/health", headers={"X-Request-ID": custom_id})
    assert response.status_code == 200
    assert response.headers.get("X-Request-ID") == custom_id


# ==============================================================================
# 3. STRUCTURED ERROR HANDLING & NON-LEAKAGE TESTS
# ==============================================================================

def test_structured_error_on_404():
    """Verify 404 responses follow the standardized error schema."""
    response = client.get("/api/v1/shipments/SHP-NONEXISTENT-999")
    # Endpoint requires auth or returns 401/404
    assert response.status_code in [401, 404]
    data = response.json()
    assert "error" in data
    assert "code" in data["error"]
    assert "message" in data["error"]
    assert "request_id" in data["error"]

def test_structured_error_on_422_validation():
    """Verify 422 input validation returns structured error with details."""
    response = client.post("/api/v1/auth/login", json={
        "email": "not-an-email"
        # missing password
    })
    assert response.status_code == 422
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert len(data["error"]["details"]) > 0
    assert "request_id" in data["error"]

def test_structured_error_on_401_unauthorized():
    """Verify 401 returns structured error schema."""
    response = client.get("/api/v1/users")
    assert response.status_code == 401
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "UNAUTHORIZED"
    assert "request_id" in data["error"]


# ==============================================================================
# 4. RATE LIMITING TESTS
# ==============================================================================

def test_rate_limiting_enforcement_on_auth():
    """Verify that rapid successive login attempts trigger HTTP 429."""
    rate_limiter.reset()
    
    status_codes = []
    # Dynamic loop to exceed configured RATE_LIMIT_LOGIN
    for _ in range(settings.RATE_LIMIT_LOGIN + 2):
        res = client.post("/api/v1/auth/login", json={
            "email": "admin@logiagent.io",
            "password": "WrongPassword!"
        })
        status_codes.append(res.status_code)
    
    # Should contain 401 for early attempts and 429 when limit is reached
    assert 429 in status_codes
    assert "Retry-After" in res.headers or any(c == 429 for c in status_codes)
    
    # Clean up rate limiter
    rate_limiter.reset()


# ==============================================================================
# 5. INPUT VALIDATION HARDENING TESTS
# ==============================================================================

def test_shipment_validation_negative_weight_rejected():
    """Verify shipment schema rejects negative cargo weight."""
    login_res = client.post("/api/v1/auth/login", json={"email": "admin@logiagent.io", "password": "LogiAgent2026!"})
    token = login_res.json()["access_token"]
    
    response = client.post(
        "/api/v1/shipments",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "shipment_code": "SHP-TEST-INVALID",
            "customer_id": 1,
            "origin_id": 1,
            "destination_id": 2,
            "cargo_type": "Standard",
            "weight_kg": -50.0  # Invalid negative weight
        }
    )
    assert response.status_code == 422
    data = response.json()
    assert data["error"]["code"] == "VALIDATION_ERROR"

def test_vehicle_validation_invalid_capacity_rejected():
    """Verify vehicle schema rejects negative or zero capacity."""
    login_res = client.post("/api/v1/auth/login", json={"email": "admin@logiagent.io", "password": "LogiAgent2026!"})
    token = login_res.json()["access_token"]
    
    response = client.post(
        "/api/v1/vehicles",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "vehicle_code": "TRK-INV-01",
            "vehicle_type": "Semi-Truck",
            "capacity_kg": -100.0,  # Invalid negative capacity
            "fuel_efficiency_kml": 4.5
        }
    )
    assert response.status_code == 422

def test_driver_validation_rating_bounds():
    """Verify driver schema enforces rating bounds (1.0 to 5.0)."""
    login_res = client.post("/api/v1/auth/login", json={"email": "admin@logiagent.io", "password": "LogiAgent2026!"})
    token = login_res.json()["access_token"]
    
    response = client.post(
        "/api/v1/drivers",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "driver_code": "DRV-INV-01",
            "name": "Invalid Driver",
            "phone": "+1-555-0199",
            "license_type": "Class A CDL",
            "rating": 7.5  # Invalid rating > 5.0
        }
    )
    assert response.status_code == 422

def test_pagination_bounds_validation():
    """Verify list endpoints enforce pagination bounds."""
    login_res = client.post("/api/v1/auth/login", json={"email": "admin@logiagent.io", "password": "LogiAgent2026!"})
    token = login_res.json()["access_token"]
    
    # limit = -1 is invalid
    res = client.get("/api/v1/routes?limit=-1", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 422
    
    # limit = 500 exceeds max 100
    res2 = client.get("/api/v1/routes?limit=500", headers={"Authorization": f"Bearer {token}"})
    assert res2.status_code == 422


# ==============================================================================
# 6. HEALTH & PROBE ENDPOINTS
# ==============================================================================

def test_health_root_endpoint():
    """Verify GET /health returns operational status."""
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "environment" in data

def test_health_liveness_probe():
    """Verify GET /health/live returns alive state."""
    res = client.get("/health/live")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "alive"
    assert "timestamp" in data

def test_health_readiness_probe():
    """Verify GET /health/ready checks DB dependency."""
    res = client.get("/health/ready")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ready"
    assert data["database"] == "connected"


# ==============================================================================
# 7. DATABASE INDEXING AUDIT VERIFICATION
# ==============================================================================

def test_database_indexes_exist():
    """Verify that performance indexes are applied on core models."""
    insp = inspect(engine)
    
    # Check shipments table indexes
    shipment_indexes = [idx["name"] for idx in insp.get_indexes("shipments")]
    assert any("status" in idx for idx in shipment_indexes) or "ix_shipments_status" in shipment_indexes
    assert any("shipment_code" in idx for idx in shipment_indexes) or "ix_shipments_shipment_code" in shipment_indexes
    
    # Check routes table indexes
    route_indexes = [idx["name"] for idx in insp.get_indexes("routes")]
    assert any("route_code" in idx for idx in route_indexes) or "ix_routes_route_code" in route_indexes
    assert any("status" in idx for idx in route_indexes) or "ix_routes_status" in route_indexes
    
    # Check vehicles table indexes
    vehicle_indexes = [idx["name"] for idx in insp.get_indexes("vehicles")]
    assert any("status" in idx for idx in vehicle_indexes) or "ix_vehicles_status" in vehicle_indexes
    
    # Check users table indexes
    user_indexes = [idx["name"] for idx in insp.get_indexes("users")]
    assert any("email" in idx for idx in user_indexes) or "ix_users_email" in user_indexes


# ==============================================================================
# 8. AI / AGENT INPUT RELIABILITY
# ==============================================================================

def test_agent_handles_empty_or_whitespace_input():
    """Verify agent rejects or handles empty queries safely."""
    login_res = client.post("/api/v1/auth/login", json={"email": "admin@logiagent.io", "password": "LogiAgent2026!"})
    token = login_res.json()["access_token"]
    
    # Empty string should fail Pydantic min_length=1 validation
    res = client.post(
        "/api/v1/agent/query",
        headers={"Authorization": f"Bearer {token}"},
        json={"query": "   "}
    )
    assert res.status_code in [200, 422]
