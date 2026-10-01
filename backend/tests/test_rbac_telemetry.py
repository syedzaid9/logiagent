import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.permissions import has_permission, get_role_permissions

client = TestClient(app)

def get_token(email: str, password: str = "LogiAgent2026!") -> str:
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, f"Login failed for {email}: {res.text}"
    return res.json()["access_token"]

# ==============================================================================
# 1. FLEET MANAGER TELEMETRY & STATS AUTHORIZATION TESTS
# ==============================================================================

def test_fleet_manager_login_and_role_identity():
    """Verifies Fleet Manager authentication returns proper role and permissions."""
    res = client.post("/api/v1/auth/login", json={
        "email": "fleet@logiagent.io",
        "password": "LogiAgent2026!"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["user"]["role"] == "Fleet Manager"
    assert data["user"]["email"] == "fleet@logiagent.io"
    assert "telemetry:read" in data["user"]["permissions"] or "routes:read" in data["user"]["permissions"]
    assert "vehicles:read" in data["user"]["permissions"]
    assert "drivers:read" in data["user"]["permissions"]

def test_fleet_manager_route_telemetry_stats_success():
    """Verifies Fleet Manager can read route telemetry / corridor statistics (HTTP 200)."""
    token = get_token("fleet@logiagent.io")
    res = client.get("/api/v1/routes/stats", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert "total_routes" in data
    assert "active_routes" in data
    assert "completed_routes" in data

def test_fleet_manager_fleet_stats_success():
    """Verifies Fleet Manager can read vehicle fleet statistics (HTTP 200)."""
    token = get_token("fleet@logiagent.io")
    res = client.get("/api/v1/vehicles/stats", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert "total_vehicles" in data
    assert "available_vehicles" in data
    assert "in_transit_vehicles" in data

def test_fleet_manager_driver_stats_success():
    """Verifies Fleet Manager can read driver roster statistics (HTTP 200)."""
    token = get_token("fleet@logiagent.io")
    res = client.get("/api/v1/drivers/stats", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert "total_drivers" in data
    assert "available_drivers" in data
    assert "on_duty_drivers" in data

def test_fleet_manager_full_dashboard_modules_access():
    """Verifies Fleet Manager has access to all operational modules on the dashboard."""
    token = get_token("fleet@logiagent.io")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Routes / Telemetry
    assert client.get("/api/v1/routes", headers=headers).status_code == 200
    # 2. Vehicle Fleet
    assert client.get("/api/v1/vehicles", headers=headers).status_code == 200
    # 3. Driver Roster
    assert client.get("/api/v1/drivers", headers=headers).status_code == 200
    # 4. Analytics
    assert client.get("/api/v1/analytics/dashboard", headers=headers).status_code == 200
    # 5. Documents / Maintenance SOPs
    assert client.get("/api/v1/rag/documents", headers=headers).status_code == 200
    # 6. Notifications / Alerts
    assert client.get("/api/v1/notifications", headers=headers).status_code == 200
    # 7. AI Alerts
    assert client.get("/api/v1/ai/alerts", headers=headers).status_code == 200

# ==============================================================================
# 2. AUTHORIZATION ACROSS ROLES FOR TELEMETRY / STATS
# ==============================================================================

def test_admin_telemetry_access():
    """Verifies Admin has access to route telemetry stats (HTTP 200)."""
    token = get_token("admin@logiagent.io")
    res = client.get("/api/v1/routes/stats", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200

def test_logistics_manager_telemetry_access():
    """Verifies Logistics Manager has access to route telemetry stats (HTTP 200)."""
    token = get_token("manager@logiagent.io")
    res = client.get("/api/v1/routes/stats", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200

def test_dispatcher_telemetry_access():
    """Verifies Dispatcher has access to route telemetry stats (HTTP 200)."""
    token = get_token("dispatcher@logiagent.io")
    res = client.get("/api/v1/routes/stats", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200

def test_driver_unauthorized_from_route_stats():
    """Verifies Driver role is forbidden from viewing global route telemetry stats (HTTP 403)."""
    token = get_token("driver@logiagent.io")
    res = client.get("/api/v1/routes/stats", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 403
    assert "Operation requires one of the following roles" in res.json()["detail"]

def test_driver_unauthorized_from_vehicle_stats():
    """Verifies Driver role is forbidden from viewing fleet stats (HTTP 403)."""
    token = get_token("driver@logiagent.io")
    res = client.get("/api/v1/vehicles/stats", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 403

def test_driver_unauthorized_from_driver_stats():
    """Verifies Driver role is forbidden from viewing driver roster stats (HTTP 403)."""
    token = get_token("driver@logiagent.io")
    res = client.get("/api/v1/drivers/stats", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 403

# ==============================================================================
# 3. LEAST PRIVILEGE / SECURITY BOUNDARIES FOR FLEET MANAGER
# ==============================================================================

def test_fleet_manager_cannot_manage_users():
    """Verifies Fleet Manager cannot access user governance list or policy modification."""
    token = get_token("fleet@logiagent.io")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Attempt user list
    res = client.get("/api/v1/users", headers=headers)
    assert res.status_code == 403

    # Attempt policy update
    res_pol = client.put("/api/v1/users/policies/Admin", headers=headers, json={
        "requires_approval": False,
        "allowed_approver_roles": ["Fleet Manager"]
    })
    assert res_pol.status_code == 403

def test_fleet_manager_cannot_create_or_cancel_shipments():
    """Verifies Fleet Manager cannot create or cancel commercial shipments."""
    token = get_token("fleet@logiagent.io")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Attempt shipment creation
    res = client.post("/api/v1/shipments", headers=headers, json={
        "shipment_code": "FM-ILLEGAL-001",
        "customer_id": 1,
        "origin_id": 1,
        "destination_id": 2,
        "cargo_type": "Machinery",
        "weight_kg": 2000
    })
    assert res.status_code == 403

    # Attempt shipment deletion/cancel
    res_del = client.delete("/api/v1/shipments/SHP-1001", headers=headers)
    assert res_del.status_code == 403

def test_canonical_role_permissions_consistency():
    """Verifies that has_permission and get_role_permissions correctly reflect Fleet Manager rights."""
    assert has_permission("Fleet Manager", "telemetry:read") is True
    assert has_permission("Fleet Manager", "routes:read") is True
    assert has_permission("Fleet Manager", "vehicles:read") is True
    assert has_permission("Fleet Manager", "vehicles:manage") is True
    assert has_permission("Fleet Manager", "drivers:read") is True
    assert has_permission("Fleet Manager", "drivers:manage") is True
    assert has_permission("Fleet Manager", "analytics:read") is True
    
    # Fleet Manager must NOT have admin governance permissions
    assert has_permission("Fleet Manager", "users:manage") is False
    assert has_permission("Fleet Manager", "roles:manage") is False
    assert has_permission("Fleet Manager", "policies:manage") is False
    assert has_permission("Fleet Manager", "system:settings") is False
