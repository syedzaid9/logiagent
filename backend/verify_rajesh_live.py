import requests
import json

BASE = "http://127.0.0.1:8000"

print("==================================================")
print("LOGIAGENT LIVE ARCHITECTURAL AUTH & RAJESH VERIFICATION")
print("==================================================")

# 1. Admin logs in
admin_login = requests.post(f"{BASE}/api/v1/auth/login", json={"email": "admin@logiagent.io", "password": "admin123"})
if admin_login.status_code != 200:
    admin_login = requests.post(f"{BASE}/api/v1/auth/login", json={"email": "admin@logiagent.io", "password": "LogiAgent2026!"})
print("1. Admin Login Status:", admin_login.status_code)
if admin_login.status_code != 200:
    print("Admin login failed:", admin_login.text)
    exit(1)
admin_token = admin_login.json()["access_token"]
admin_headers = {"Authorization": f"Bearer {admin_token}"}

# 2. Get Users list
users_res = requests.get(f"{BASE}/api/v1/users", headers=admin_headers)
users = users_res.json()
print(f"2. Total Users in DB: {len(users)}")
for u in users:
    auth_status = "Configured" if u.get("has_usable_password") else ("Invitation Pending" if u.get("has_activation_token") else "Not Configured")
    print(f"   - ID: {u['id']} | Email: {u['email']} | Role: {u['role']} | Auth: {auth_status} | Driver ID: {u.get('driver_id')}")

rajesh_user = next((u for u in users if u["email"] == "rajesh@logiagent.io"), None)
raj_user = next((u for u in users if u.get("username") == "raj" or u.get("email") == "raj@logiagent.io"), None)

if not rajesh_user:
    print("ERROR: rajesh@logiagent.io not found!")
    exit(1)

print(f"\nTarget Rajesh User: ID={rajesh_user['id']}, Email={rajesh_user['email']}")

# 3. Admin Reissues Invitation for Rajesh
print("\n3. Admin Reissuing Invitation (NO PASSWORD SET BY ADMIN)...")
reissue_res = requests.post(f"{BASE}/api/v1/users/{rajesh_user['id']}/reissue-invitation", headers=admin_headers)
print("   Reissue Status Code:", reissue_res.status_code)
reissue_data = reissue_res.json()
print("   Reissue Response Payload (Keys):", list(reissue_data.keys()))
print("   Invitation URL:", reissue_data.get("development_invitation_url"))
print("   Invitation Token:", reissue_data.get("activation_token"))
assert "password" not in reissue_data, "Admin response must NEVER contain password!"
assert "temporary_password" not in reissue_data, "Admin response must NEVER contain temporary_password!"

token = reissue_data.get("activation_token")
inv_url = reissue_data.get("development_invitation_url")

# 4. Rajesh opens invitation link (Validate Token)
print("\n4. Rajesh opens /activate-account?token=...")
token_check = requests.get(f"{BASE}/api/v1/auth/invitation/{token}")
print("   Token Validation Status:", token_check.status_code)
token_data = token_check.json()
print("   Token Validation Data:", token_data)
assert token_data["valid"] is True
assert token_data["email"] == "rajesh@logiagent.io"

# 5. Rajesh sets his OWN password from activation modal
new_pw = "RajeshPass2026!"
print(f"\n5. Rajesh sets his own password ({new_pw}) on activation page...")
accept_res = requests.post(f"{BASE}/api/v1/auth/accept-invitation", json={
    "token": token,
    "password": new_pw,
    "confirm_password": new_pw
})
print("   Set Password Status:", accept_res.status_code)
accept_data = accept_res.json()
print("   Set Password Response:", accept_data)
assert accept_res.status_code == 200

# 6. Verify single-use token invalidated
print("\n6. Verifying single-use token invalidation...")
reuse_check = requests.post(f"{BASE}/api/v1/auth/accept-invitation", json={
    "token": token,
    "password": new_pw,
    "confirm_password": new_pw
})
print("   Reuse Attempt Status (Expect 400):", reuse_check.status_code)
assert reuse_check.status_code == 400

# 7. Rajesh logs in with newly created password
print("\n7. Rajesh logs in with his newly created password...")
driver_login = requests.post(f"{BASE}/api/v1/auth/login", json={
    "email": "rajesh@logiagent.io",
    "password": new_pw
})
print("   Login Status:", driver_login.status_code)
assert driver_login.status_code == 200
driver_token = driver_login.json()["access_token"]
driver_headers = {"Authorization": f"Bearer {driver_token}"}
print("   Login Success! Token obtained.")

# 8. Check Rajesh Driver Profile & Linkage
print("\n8. Checking Driver Profile Linkage and Driver Portal...")
portal_res = requests.get(f"{BASE}/api/v1/analytics/driver-portal", headers=driver_headers)
print("   Driver Portal Status:", portal_res.status_code)
if portal_res.status_code == 200:
    portal_data = portal_res.json()
    print("   Driver Portal Data Keys:", list(portal_data.keys()))
    print("   Driver Name:", portal_data.get("driver_name"))
    print("   Active Shipments:", len(portal_data.get("active_shipments", [])))
    print("   Completed Today:", portal_data.get("completed_today"))

# 9. Check Driver Shipments
print("\n9. Checking Driver Shipments Access...")
shipments_res = requests.get(f"{BASE}/api/v1/shipments", headers=driver_headers)
print("   Shipments Status:", shipments_res.status_code)
if shipments_res.status_code == 200:
    shipments = shipments_res.json()
    print(f"   Total accessible shipments: {len(shipments)}")

# 10. Check Driver RBAC restriction on Admin routes
print("\n10. Checking Driver RBAC Enforcement (Cannot access Admin User Management)...")
admin_access_res = requests.get(f"{BASE}/api/v1/users", headers=driver_headers)
print("   Driver Access to /api/v1/users (Expect 403):", admin_access_res.status_code)
assert admin_access_res.status_code == 403, f"Expected 403 Forbidden, got {admin_access_res.status_code}"

# 11. Self-Service Change Password Test for Rajesh
print("\n11. Testing Rajesh Self-Service Change Password...")
newer_pw = "RajeshNewPass2026!"
change_pw_res = requests.post(f"{BASE}/api/v1/auth/change-password", headers=driver_headers, json={
    "current_password": new_pw,
    "new_password": newer_pw,
    "confirm_new_password": newer_pw
})
print("   Change Password Status:", change_pw_res.status_code, change_pw_res.json())
assert change_pw_res.status_code == 200

# Re-login with new password
relogin_res = requests.post(f"{BASE}/api/v1/auth/login", json={
    "email": "rajesh@logiagent.io",
    "password": newer_pw
})
print("   Re-login with changed password Status:", relogin_res.status_code)
assert relogin_res.status_code == 200

print("\n==================================================")
print("ALL LIVE VERIFICATION CHECKS PASSED SUCCESSFULLY!")
print("==================================================")
