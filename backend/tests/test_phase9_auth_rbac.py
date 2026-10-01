import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import create_access_token, get_password_hash, verify_password
from app.core.permissions import has_permission, get_role_permissions
from app.core.database import SessionLocal
from app.models.user import User
from app.models.driver import Driver
from app.models.vehicle import Vehicle
from app.models.shipment import Shipment
from app.models.route import Route

client = TestClient(app)

@pytest.fixture(scope="module")
def db():
    session = SessionLocal()
    yield session
    session.close()

# ==============================================================================
# 1. AUTHENTICATION TESTS
# ==============================================================================

def test_admin_login_success():
    response = client.post("/api/v1/auth/login", json={
        "email": "admin@logiagent.io",
        "password": "LogiAgent2026!"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["role"] == "Admin"
    assert len(data["user"]["permissions"]) > 0

def test_driver_login_success():
    response = client.post("/api/v1/auth/login", json={
        "email": "driver@logiagent.io",
        "password": "LogiAgent2026!"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["role"] == "Driver"
    assert data["user"]["driver_id"] is not None

def test_login_invalid_password_returns_401():
    response = client.post("/api/v1/auth/login", json={
        "email": "admin@logiagent.io",
        "password": "WrongPassword123!"
    })
    assert response.status_code == 401
    assert "detail" in response.json()

def test_login_nonexistent_user_returns_401():
    response = client.post("/api/v1/auth/login", json={
        "email": "nonexistent@logiagent.io",
        "password": "SomePassword123!"
    })
    assert response.status_code == 401

def test_unauthenticated_requests_return_401():
    protected_endpoints = [
        "/api/v1/shipments",
        "/api/v1/routes",
        "/api/v1/vehicles",
        "/api/v1/drivers",
        "/api/v1/users",
        "/api/v1/analytics/dashboard",
        "/api/v1/auth/me"
    ]
    for ep in protected_endpoints:
        res = client.get(ep)
        assert res.status_code == 401, f"Endpoint {ep} should return 401 when called without token"

def test_auth_me_returns_profile_and_permissions():
    login_res = client.post("/api/v1/auth/login", json={"email": "admin@logiagent.io", "password": "LogiAgent2026!"})
    token = login_res.json()["access_token"]
    res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert data["email"] == "admin@logiagent.io"
    assert data["role"] == "Admin"
    assert "users:manage" in data["permissions"]

def test_auth_logout():
    login_res = client.post("/api/v1/auth/login", json={"email": "admin@logiagent.io", "password": "LogiAgent2026!"})
    token = login_res.json()["access_token"]
    res = client.post("/api/v1/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.json()["success"] is True

# ==============================================================================
# 2. RBAC & PERMISSION TESTS
# ==============================================================================

def test_driver_forbidden_from_user_management():
    login_res = client.post("/api/v1/auth/login", json={"email": "driver@logiagent.io", "password": "LogiAgent2026!"})
    token = login_res.json()["access_token"]
    res = client.get("/api/v1/users", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 403

def test_driver_forbidden_from_creating_shipments():
    login_res = client.post("/api/v1/auth/login", json={"email": "driver@logiagent.io", "password": "LogiAgent2026!"})
    token = login_res.json()["access_token"]
    res = client.post("/api/v1/shipments", headers={"Authorization": f"Bearer {token}"}, json={
        "shipment_code": "FORBIDDEN-001",
        "customer_id": 1,
        "origin_id": 1,
        "destination_id": 2,
        "cargo_type": "Electronics",
        "weight_kg": 5000
    })
    assert res.status_code == 403

def test_dispatcher_forbidden_from_modifying_policies():
    login_res = client.post("/api/v1/auth/login", json={"email": "dispatcher@logiagent.io", "password": "LogiAgent2026!"})
    token = login_res.json()["access_token"]
    res = client.put("/api/v1/users/policies/Admin", headers={"Authorization": f"Bearer {token}"}, json={
        "requires_approval": False,
        "allowed_approver_roles": ["Dispatcher"]
    })
    assert res.status_code == 403

def test_admin_has_all_permissions():
    assert has_permission("Admin", "shipments:create") is True
    assert has_permission("Admin", "users:manage") is True
    assert has_permission("Admin", "routes:optimize") is True
    assert has_permission("Admin", "nonexistent:permission") is True

def test_driver_has_limited_permissions():
    assert has_permission("Driver", "shipments:read_own") is True
    assert has_permission("Driver", "shipments:create") is False
    assert has_permission("Driver", "users:manage") is False
    assert has_permission("Driver", "roles:manage") is False

# ==============================================================================
# 3. DATA-LEVEL AUTHORIZATION TESTS
# ==============================================================================

def test_driver_receives_only_assigned_shipments():
    # Manager token
    mgr_res = client.post("/api/v1/auth/login", json={"email": "manager@logiagent.io", "password": "LogiAgent2026!"})
    mgr_token = mgr_res.json()["access_token"]
    all_shipments = client.get("/api/v1/shipments", headers={"Authorization": f"Bearer {mgr_token}"}).json()

    # Driver token
    drv_res = client.post("/api/v1/auth/login", json={"email": "driver@logiagent.io", "password": "LogiAgent2026!"})
    drv_data = drv_res.json()
    drv_token = drv_data["access_token"]
    driver_id = drv_data["user"]["driver_id"]

    drv_shipments = client.get("/api/v1/shipments", headers={"Authorization": f"Bearer {drv_token}"}).json()
    
    assert len(drv_shipments) <= len(all_shipments)
    for s in drv_shipments:
        if s.get("driver_id"):
            assert s["driver_id"] == driver_id

def test_driver_cannot_access_unassigned_shipment_by_code():
    mgr_res = client.post("/api/v1/auth/login", json={"email": "manager@logiagent.io", "password": "LogiAgent2026!"})
    mgr_token = mgr_res.json()["access_token"]
    all_shipments = client.get("/api/v1/shipments", headers={"Authorization": f"Bearer {mgr_token}"}).json()

    drv_res = client.post("/api/v1/auth/login", json={"email": "driver@logiagent.io", "password": "LogiAgent2026!"})
    drv_data = drv_res.json()
    drv_token = drv_data["access_token"]
    driver_id = drv_data["user"]["driver_id"]

    unassigned_shp = next((s for s in all_shipments if s.get("driver_id") != driver_id), None)
    if unassigned_shp:
        res = client.get(f"/api/v1/shipments/{unassigned_shp['shipment_code']}", headers={"Authorization": f"Bearer {drv_token}"})
        assert res.status_code == 403

def test_driver_cannot_access_other_driver_profile():
    drv_res = client.post("/api/v1/auth/login", json={"email": "driver@logiagent.io", "password": "LogiAgent2026!"})
    drv_token = drv_res.json()["access_token"]

    res = client.get("/api/v1/drivers/DRV-02", headers={"Authorization": f"Bearer {drv_token}"})
    assert res.status_code in [403, 404]

# ==============================================================================
# 4. ACCOUNT LIFECYCLE & PRIVILEGE ESCALATION
# ==============================================================================

def test_user_self_approval_blocked():
    admin_res = client.post("/api/v1/auth/login", json={"email": "admin@logiagent.io", "password": "LogiAgent2026!"})
    admin_token = admin_res.json()["access_token"]
    admin_id = admin_res.json()["user"]["id"]

    res = client.post(f"/api/v1/users/{admin_id}/approve", headers={"Authorization": f"Bearer {admin_token}"}, json={
        "approved": True
    })
    assert res.status_code == 400
    assert "cannot approve their own" in res.json()["detail"].lower()

def test_account_suspension_blocks_api_access():
    admin_res = client.post("/api/v1/auth/login", json={"email": "admin@logiagent.io", "password": "LogiAgent2026!"})
    admin_token = admin_res.json()["access_token"]

    # Provision temporary user
    prov_res = client.post("/api/v1/users/provision", headers={"Authorization": f"Bearer {admin_token}"}, json={
        "email": "temp_susp_test@logiagent.io",
        "full_name": "Temporary Test User",
        "role": "Analyst",
        "auto_approve": True
    })
    assert prov_res.status_code == 201
    temp_user_id = prov_res.json()["user"]["id"]
    token = prov_res.json()["activation_token"]

    # Activate
    client.post("/api/v1/auth/accept-invitation", json={
        "token": token,
        "password": "TempPassword2026!"
    })

    # Login
    user_login = client.post("/api/v1/auth/login", json={
        "email": "temp_susp_test@logiagent.io",
        "password": "TempPassword2026!"
    })
    user_token = user_login.json()["access_token"]

    # Suspend user
    susp_res = client.post(f"/api/v1/users/{temp_user_id}/suspend", headers={"Authorization": f"Bearer {admin_token}"})
    assert susp_res.status_code == 200

    # User attempts to call API with token
    blocked_call = client.get("/api/v1/analytics/dashboard", headers={"Authorization": f"Bearer {user_token}"})
    assert blocked_call.status_code == 403
    assert "suspended" in blocked_call.json()["detail"].lower()

    # Clean up
    db = SessionLocal()
    try:
        db.query(User).filter(User.id == temp_user_id).delete()
        db.commit()
    finally:
        db.close()
