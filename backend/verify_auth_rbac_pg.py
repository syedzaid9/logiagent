import requests

BASE = "http://localhost:8000/api/v1"

def run_tests():
    print("--- 1. Testing Unauthenticated Access ---")
    r_unauth = requests.get(f"{BASE}/auth/me")
    assert r_unauth.status_code == 401, f"Expected 401, got {r_unauth.status_code}"
    print("[PASS] Unauthenticated /auth/me returned 401")

    print("\n--- 2. Testing Invalid Credentials ---")
    r_bad = requests.post(f"{BASE}/auth/login", json={"email": "admin@logiagent.io", "password": "WrongPassword123!"})
    assert r_bad.status_code == 401, f"Expected 401, got {r_bad.status_code}"
    print("[PASS] Bad credentials returned 401")

    print("\n--- 3. Testing Login for all 7 Roles ---")
    roles = [
        ("admin@logiagent.io", "Admin"),
        ("manager@logiagent.io", "Logistics Manager"),
        ("dispatcher@logiagent.io", "Dispatcher"),
        ("fleet@logiagent.io", "Fleet Manager"),
        ("driver@logiagent.io", "Driver"),
        ("analyst@logiagent.io", "Analyst"),
        ("ops@logiagent.io", "Operations Team"),
    ]

    tokens = {}
    for email, role_name in roles:
        res = requests.post(f"{BASE}/auth/login", json={"email": email, "password": "LogiAgent2026!"})
        assert res.status_code == 200, f"Failed login for {email}: {res.text}"
        data = res.json()
        token = data["access_token"]
        tokens[role_name] = token
        
        # Profile retrieval
        prof_res = requests.get(f"{BASE}/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert prof_res.status_code == 200
        prof = prof_res.json()
        assert prof["email"] == email
        assert prof["role"] == role_name
        print(f"[PASS] {role_name} ({email}) logged in successfully. User ID: {prof['id']}")

    print("\n--- 4. Testing RBAC Permission Enforcement ---")
    # Driver cannot view all users (requires users:manage/read)
    driver_headers = {"Authorization": f"Bearer {tokens['Driver']}"}
    r_driver_users = requests.get(f"{BASE}/users", headers=driver_headers)
    assert r_driver_users.status_code == 403, f"Driver expected 403 on /users, got {r_driver_users.status_code}"
    print(f"[PASS] Driver access to /users correctly rejected with 403")

    # Admin CAN view all users
    admin_headers = {"Authorization": f"Bearer {tokens['Admin']}"}
    r_admin_users = requests.get(f"{BASE}/users", headers=admin_headers)
    assert r_admin_users.status_code == 200, f"Admin expected 200 on /users, got {r_admin_users.status_code}"
    user_list = r_admin_users.json()
    print(f"[PASS] Admin access to /users returned 200 with {len(user_list)} users")

    # Driver can view their own driver profile and shipments
    r_driver_shipments = requests.get(f"{BASE}/shipments", headers=driver_headers)
    assert r_driver_shipments.status_code == 200
    print(f"[PASS] Driver accessed /shipments (scoped) successfully")

    print("\n--- 5. Testing Profile Update ---")
    update_res = requests.patch(
        f"{BASE}/users/me",
        headers=admin_headers,
        json={"full_name": "Sarah Jenkins (Admin - Verified)"}
    )
    assert update_res.status_code == 200
    assert update_res.json()["full_name"] == "Sarah Jenkins (Admin - Verified)"
    print("[PASS] Profile update successful")

    # Revert name
    requests.patch(
        f"{BASE}/users/me",
        headers=admin_headers,
        json={"full_name": "Sarah Jenkins (Admin)"}
    )

    print("\n=== All Auth & RBAC Tests Passed Successfully! ===")

if __name__ == "__main__":
    run_tests()
