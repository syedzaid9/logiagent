import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import create_access_token

client = TestClient(app)

def test_settings_rbac_and_crud():
    # 1. Test unauthenticated request is blocked
    resp_unauth = client.get("/api/v1/settings")
    assert resp_unauth.status_code == 401

    # 2. Driver role (should be forbidden from modifying settings)
    driver_token = create_access_token(subject="driver@logiagent.io", role="Driver")
    resp_driver_put = client.put(
        "/api/v1/settings",
        headers={"Authorization": f"Bearer {driver_token}"},
        json={"category": "general", "settings": {"organization_name": "Hacked"}}
    )
    assert resp_driver_put.status_code == 403

    # 3. Admin role (authorized)
    admin_token = create_access_token(subject="admin@logiagent.io", role="Admin")
    headers = {"Authorization": f"Bearer {admin_token}"}

    # Fetch settings
    resp_get = client.get("/api/v1/settings", headers=headers)
    assert resp_get.status_code == 200
    data = resp_get.json()
    assert "settings" in data
    assert "general" in data["settings"]
    assert "shipments" in data["settings"]
    assert "fleet" in data["settings"]
    assert "ai_rag" in data["settings"]
    assert "notifications" in data["settings"]
    assert "security" in data["settings"]

    # Update category settings
    resp_put = client.put(
        "/api/v1/settings",
        headers=headers,
        json={
            "category": "shipments",
            "settings": {
                "sla_target_hours": 36,
                "warning_delay_threshold_mins": 25
            }
        }
    )
    assert resp_put.status_code == 200
    updated_data = resp_put.json()
    assert updated_data["settings"]["shipments"]["sla_target_hours"] == 36
    assert updated_data["settings"]["shipments"]["warning_delay_threshold_mins"] == 25

    # Verify persistence by fetching again
    resp_get2 = client.get("/api/v1/settings", headers=headers)
    assert resp_get2.status_code == 200
    assert resp_get2.json()["settings"]["shipments"]["sla_target_hours"] == 36

    # Test reset category back to default
    resp_reset = client.post(
        "/api/v1/settings/reset",
        headers=headers,
        json={"category": "shipments"}
    )
    assert resp_reset.status_code == 200
    assert resp_reset.json()["settings"]["shipments"]["sla_target_hours"] == 48
