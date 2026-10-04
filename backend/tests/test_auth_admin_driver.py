import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal
from app.models.user import User
from app.models.driver import Driver

client = TestClient(app)

@pytest.fixture(scope="module")
def admin_token():
    res = client.post("/api/v1/auth/login", json={
        "email": "admin@logiagent.io",
        "password": "LogiAgent2026!"
    })
    assert res.status_code == 200
    return res.json()["access_token"]

# ==============================================================================
# 1. ADMIN CREATES USER & USER SETS OWN PASSWORD VIA INVITATION
# ==============================================================================

def test_admin_creates_driver_user_sets_own_password(admin_token):
    """
    Admin provisions a driver with an invitation token.
    Admin never sees or sets the password.
    User establishes their own password via invitation acceptance.
    """
    email = "test_driver_invitation@logiagent.io"

    db = SessionLocal()
    try:
        db.query(User).filter(User.email == email).delete()
        db.commit()
    finally:
        db.close()

    # 1. Admin creates user
    res = client.post(
        "/api/v1/users/provision",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "email": email,
            "full_name": "Test Driver Invite",
            "role": "Driver",
            "auto_approve": True
        }
    )
    assert res.status_code == 201
    data = res.json()
    assert data["success"] is True
    assert data["activation_token"] is not None
    assert "temporary_password" not in data or data.get("temporary_password") is None
    assert data["development_invitation_url"] is not None
    assert data["user"]["role"] == "Driver"
    assert data["user"]["account_status"] == "Pending_Activation"
    assert data["user"]["approval_status"] == "Approved"
    assert data["user"]["driver_id"] is not None

    invitation_token = data["activation_token"]
    user_id = data["user"]["id"]

    # 2. Validate invitation endpoint
    check_inv = client.get(f"/api/v1/auth/invitation/{invitation_token}")
    assert check_inv.status_code == 200
    assert check_inv.json()["valid"] is True
    assert check_inv.json()["email"] == email

    # 3. User sets their own password
    chosen_password = "MySecureDriverPass2026!"
    accept_res = client.post("/api/v1/auth/accept-invitation", json={
        "token": invitation_token,
        "password": chosen_password,
        "full_name": "Test Driver Invite Verified"
    })
    assert accept_res.status_code == 200
    acc_data = accept_res.json()
    assert acc_data["user"]["account_status"] == "Active"
    assert acc_data["user"]["has_usable_password"] is True
    assert acc_data["user"]["has_activation_token"] is False
    assert acc_data["access_token"] is not None

    # 4. Driver logs in with their chosen password
    login_res = client.post("/api/v1/auth/login", json={
        "email": email,
        "password": chosen_password
    })
    assert login_res.status_code == 200
    driver_token = login_res.json()["access_token"]

    # 5. Driver accesses driver portal telemetry
    portal_res = client.get("/api/v1/analytics/driver-portal", headers={"Authorization": f"Bearer {driver_token}"})
    assert portal_res.status_code == 200
    assert portal_res.json()["driver"]["id"] == data["user"]["driver_id"]

    # 6. Driver cannot access Admin RBAC
    rbac_res = client.get("/api/v1/users", headers={"Authorization": f"Bearer {driver_token}"})
    assert rbac_res.status_code == 403

    # Clean up
    db = SessionLocal()
    try:
        db.query(User).filter(User.id == user_id).delete()
        db.commit()
    finally:
        db.close()


def test_user_changes_own_password(admin_token):
    """
    Authenticated user changes their own password via /api/v1/auth/change-password.
    """
    email = "test_change_pwd@logiagent.io"

    db = SessionLocal()
    try:
        db.query(User).filter(User.email == email).delete()
        db.commit()
    finally:
        db.close()

    # 1. Register user
    reg = client.post("/api/v1/auth/register", json={
        "email": email,
        "password": "InitialPassword123!",
        "full_name": "Change Pwd User",
        "role": "Dispatcher"
    })
    assert reg.status_code == 200
    user_token = reg.json()["access_token"]
    user_id = reg.json()["user"]["id"]

    # 2. Change password with incorrect current password -> fails
    fail_res = client.post(
        "/api/v1/auth/change-password",
        headers={"Authorization": f"Bearer {user_token}"},
        json={
            "current_password": "WrongPassword!",
            "new_password": "BrandNewPassword2026!"
        }
    )
    assert fail_res.status_code == 400
    assert "current password" in fail_res.json()["detail"].lower()

    # 3. Change password with correct current password -> succeeds
    succ_res = client.post(
        "/api/v1/auth/change-password",
        headers={"Authorization": f"Bearer {user_token}"},
        json={
            "current_password": "InitialPassword123!",
            "new_password": "BrandNewPassword2026!"
        }
    )
    assert succ_res.status_code == 200
    assert succ_res.json()["success"] is True

    # 4. Old password rejected
    old_login = client.post("/api/v1/auth/login", json={
        "email": email,
        "password": "InitialPassword123!"
    })
    assert old_login.status_code == 401

    # 5. New password accepted
    new_login = client.post("/api/v1/auth/login", json={
        "email": email,
        "password": "BrandNewPassword2026!"
    })
    assert new_login.status_code == 200

    # Clean up
    db = SessionLocal()
    try:
        db.query(User).filter(User.id == user_id).delete()
        db.commit()
    finally:
        db.close()


def test_forgot_and_reset_password_flow():
    """
    User requests forgot password, receives single-use token, resets password, and logs in.
    """
    email = "test_forgot_flow@logiagent.io"

    db = SessionLocal()
    try:
        db.query(User).filter(User.email == email).delete()
        db.commit()
    finally:
        db.close()

    # 1. Register user
    reg = client.post("/api/v1/auth/register", json={
        "email": email,
        "password": "OriginalPassword123!",
        "full_name": "Forgot Flow User",
        "role": "Logistics Manager"
    })
    assert reg.status_code == 200
    user_id = reg.json()["user"]["id"]

    # 2. Request forgot password
    forgot_res = client.post("/api/v1/auth/forgot-password", json={"email": email})
    assert forgot_res.status_code == 200
    forgot_data = forgot_res.json()
    assert forgot_data["success"] is True
    assert forgot_data["reset_token"] is not None
    assert forgot_data["reset_url"] is not None
    reset_tok = forgot_data["reset_token"]

    # 3. Verify reset token info
    check_tok = client.get(f"/api/v1/auth/reset-password/{reset_tok}")
    assert check_tok.status_code == 200
    assert check_tok.json()["valid"] is True
    assert check_tok.json()["email"] == email

    # 4. Reset password with new password
    reset_res = client.post("/api/v1/auth/reset-password", json={
        "token": reset_tok,
        "password": "ResetSuccessPassword2026!"
    })
    assert reset_res.status_code == 200
    assert reset_res.json()["success"] is True

    # 5. Token is single-use: second attempt fails
    reuse_res = client.post("/api/v1/auth/reset-password", json={
        "token": reset_tok,
        "password": "AnotherAttempt123!"
    })
    assert reuse_res.status_code == 400

    # 6. Login with new reset password
    login_res = client.post("/api/v1/auth/login", json={
        "email": email,
        "password": "ResetSuccessPassword2026!"
    })
    assert login_res.status_code == 200

    # Clean up
    db = SessionLocal()
    try:
        db.query(User).filter(User.id == user_id).delete()
        db.commit()
    finally:
        db.close()


def test_expired_and_invalid_invitation_tokens(admin_token):
    """
    Expired and invalid activation tokens are rejected.
    """
    email = "test_expired_tok@logiagent.io"

    db = SessionLocal()
    try:
        db.query(User).filter(User.email == email).delete()
        db.commit()
    finally:
        db.close()

    # 1. Provision user
    prov = client.post(
        "/api/v1/users/provision",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"email": email, "full_name": "Expired Test", "role": "Dispatcher", "auto_approve": True}
    )
    assert prov.status_code == 201
    user_id = prov.json()["user"]["id"]
    token = prov.json()["activation_token"]

    # 2. Manually expire token in database
    db = SessionLocal()
    try:
        u = db.query(User).filter(User.id == user_id).first()
        u.activation_expires_at = datetime.utcnow() - timedelta(days=1)
        db.commit()
    finally:
        db.close()

    # 3. Check invitation -> invalid (expired)
    inv_check = client.get(f"/api/v1/auth/invitation/{token}")
    assert inv_check.status_code == 200
    assert inv_check.json()["valid"] is False
    assert "expired" in inv_check.json()["message"].lower()

    # 4. Attempt to accept expired token -> 400
    acc_expired = client.post("/api/v1/auth/accept-invitation", json={
        "token": token,
        "password": "ValidPassword123!"
    })
    assert acc_expired.status_code == 400
    assert "expired" in acc_expired.json()["detail"].lower()

    # 5. Nonexistent token -> 400
    acc_fake = client.post("/api/v1/auth/accept-invitation", json={
        "token": "completely_fake_token_12345",
        "password": "ValidPassword123!"
    })
    assert acc_fake.status_code == 400

    # Clean up
    db = SessionLocal()
    try:
        db.query(User).filter(User.id == user_id).delete()
        db.commit()
    finally:
        db.close()


def test_reissue_invitation_creates_fresh_token(admin_token):
    """
    Admin reissues invitation token for a user, invalidating old token.
    """
    email = "test_reissue_fresh@logiagent.io"

    db = SessionLocal()
    try:
        db.query(User).filter(User.email == email).delete()
        db.commit()
    finally:
        db.close()

    # 1. Provision user
    prov = client.post(
        "/api/v1/users/provision",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"email": email, "full_name": "Reissue Fresh User", "role": "Analyst", "auto_approve": True}
    )
    assert prov.status_code == 201
    user_id = prov.json()["user"]["id"]
    old_token = prov.json()["activation_token"]

    # 2. Reissue invitation
    reissue = client.post(
        f"/api/v1/users/{user_id}/reissue-invitation",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert reissue.status_code == 200
    new_token = reissue.json()["activation_token"]
    assert new_token != old_token
    assert reissue.json()["development_invitation_url"] is not None

    # 3. Old token rejected
    old_acc = client.post("/api/v1/auth/accept-invitation", json={
        "token": old_token,
        "password": "Password123!"
    })
    assert old_acc.status_code == 400

    # 4. New token succeeds
    new_acc = client.post("/api/v1/auth/accept-invitation", json={
        "token": new_token,
        "password": "NewUserPassword2026!"
    })
    assert new_acc.status_code == 200
    assert new_acc.json()["user"]["account_status"] == "Active"

    # Clean up
    db = SessionLocal()
    try:
        db.query(User).filter(User.id == user_id).delete()
        db.commit()
    finally:
        db.close()
