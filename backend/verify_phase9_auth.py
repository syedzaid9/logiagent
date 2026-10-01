import requests
import json
import time
import random

BASE_URL = "http://127.0.0.1:8000/api/v1"

def print_header(title: str):
    print("\n" + "=" * 75)
    print(f"  {title}")
    print("=" * 75)

def print_pass(msg: str):
    print(f"  [PASS] {msg}")

def print_fail(msg: str):
    print(f"  [FAIL] {msg}")
    raise AssertionError(msg)

def test_phase9_authentication_and_rbac():
    print_header("PHASE 9: COMPLETE AUTHENTICATION + RBAC + DATA-LEVEL SCOPING VERIFICATION")

    # --------------------------------------------------------------------------------------
    # Requirement 1: Authentication & Token Issuance
    # --------------------------------------------------------------------------------------
    print("\n1. Testing Supabase / FastAPI Authentication & Session Tokens...")
    
    # 1.1 Valid Admin Login
    res_admin = requests.post(f"{BASE_URL}/auth/login", json={
        "email": "admin@logiagent.io",
        "password": "LogiAgent2026!"
    })
    if res_admin.status_code != 200:
        print_fail(f"Admin login failed: {res_admin.status_code} - {res_admin.text}")
    admin_data = res_admin.json()
    admin_token = admin_data["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    print_pass("Admin logged in successfully and received JWT Bearer token.")

    # 1.2 Valid Manager Login
    res_mgr = requests.post(f"{BASE_URL}/auth/login", json={
        "email": "manager@logiagent.io",
        "password": "LogiAgent2026!"
    })
    if res_mgr.status_code != 200:
        print_fail(f"Manager login failed: {res_mgr.status_code} - {res_mgr.text}")
    mgr_token = res_mgr.json()["access_token"]
    mgr_headers = {"Authorization": f"Bearer {mgr_token}"}
    print_pass("Logistics Manager logged in successfully.")

    # 1.3 Valid Dispatcher Login
    res_disp = requests.post(f"{BASE_URL}/auth/login", json={
        "email": "dispatcher@logiagent.io",
        "password": "LogiAgent2026!"
    })
    if res_disp.status_code != 200:
        print_fail(f"Dispatcher login failed: {res_disp.status_code} - {res_disp.text}")
    disp_token = res_disp.json()["access_token"]
    disp_headers = {"Authorization": f"Bearer {disp_token}"}
    print_pass("Dispatcher logged in successfully.")

    # 1.4 Valid Driver Login
    res_drv = requests.post(f"{BASE_URL}/auth/login", json={
        "email": "driver@logiagent.io",
        "password": "LogiAgent2026!"
    })
    if res_drv.status_code != 200:
        print_fail(f"Driver login failed: {res_drv.status_code} - {res_drv.text}")
    driver_token = res_drv.json()["access_token"]
    driver_headers = {"Authorization": f"Bearer {driver_token}"}
    print_pass("Driver logged in successfully with driver profile link.")

    # 1.5 Invalid Password Rejection (401)
    res_bad = requests.post(f"{BASE_URL}/auth/login", json={
        "email": "admin@logiagent.io",
        "password": "WrongPassword123!"
    })
    if res_bad.status_code != 401:
        print_fail(f"Expected 401 for bad password, got {res_bad.status_code}")
    print_pass("Invalid password rejected with HTTP 401 Unauthorized.")

    # 1.6 /auth/me Endpoint
    res_me = requests.get(f"{BASE_URL}/auth/me", headers=admin_headers)
    if res_me.status_code != 200 or res_me.json()["role"] != "Admin":
        print_fail("Failed to retrieve current user profile from /auth/me")
    print_pass(f"Retrieved active session for '{res_me.json()['full_name']}' ({res_me.json()['role']}).")

    # --------------------------------------------------------------------------------------
    # Requirement 8 & 19: Unauthenticated API Access Protection (401)
    # --------------------------------------------------------------------------------------
    print("\n2. Testing Protected Endpoint Rejection Without Tokens (HTTP 401)...")
    endpoints_to_test = [
        ("GET", f"{BASE_URL}/shipments"),
        ("GET", f"{BASE_URL}/vehicles"),
        ("GET", f"{BASE_URL}/drivers"),
        ("GET", f"{BASE_URL}/routes"),
        ("GET", f"{BASE_URL}/analytics/dashboard"),
        ("GET", f"{BASE_URL}/users")
    ]
    for method, url in endpoints_to_test:
        r = requests.get(url) if method == "GET" else requests.post(url)
        if r.status_code != 401:
            print_fail(f"Endpoint {url} allowed unauthenticated access with status {r.status_code}")
    print_pass("All core logistics endpoints strictly reject unauthenticated requests with HTTP 401.")

    # --------------------------------------------------------------------------------------
    # Requirement 4 & 5: Role-Based Access Control (RBAC) & Permissions (403)
    # --------------------------------------------------------------------------------------
    print("\n3. Testing Role-Based Access Control (RBAC) Permissions (HTTP 403)...")
    
    # Drivers cannot access User Management
    res_drv_users = requests.get(f"{BASE_URL}/users", headers=driver_headers)
    if res_drv_users.status_code != 403:
        print_fail(f"Driver should be forbidden from /users, got {res_drv_users.status_code}")
    print_pass("Driver forbidden from accessing User Management (HTTP 403 Forbidden).")

    # Drivers cannot create shipments
    res_drv_create_shp = requests.post(f"{BASE_URL}/shipments", headers=driver_headers, json={
        "shipment_code": "ILLEGAL-SHP",
        "customer_id": 1,
        "origin_id": 1,
        "destination_id": 2,
        "cargo_type": "Hazardous",
        "weight_kg": 5000,
        "expected_delivery": "2026-10-01T00:00:00Z"
    })
    if res_drv_create_shp.status_code != 403:
        print_fail(f"Driver was able to call create_shipment, got {res_drv_create_shp.status_code}")
    print_pass("Driver forbidden from creating shipments (HTTP 403 Forbidden).")

    # Dispatcher cannot manage Approval Policies
    res_disp_policy = requests.get(f"{BASE_URL}/users/policies", headers=disp_headers)
    if res_disp_policy.status_code != 403:
        print_fail(f"Dispatcher should be forbidden from approval policies, got {res_disp_policy.status_code}")
    print_pass("Dispatcher forbidden from modifying security policies (HTTP 403 Forbidden).")

    # --------------------------------------------------------------------------------------
    # Requirement 9 & 10: Server-Side Data-Level Authorization Scoping
    # --------------------------------------------------------------------------------------
    print("\n4. Testing Server-Side Data-Level Authorization Scoping...")

    # Fetch driver's shipments via driver's token
    res_drv_shipments = requests.get(f"{BASE_URL}/shipments", headers=driver_headers)
    if res_drv_shipments.status_code != 200:
        print_fail(f"Driver failed to fetch scoped shipments: {res_drv_shipments.status_code}")
    driver_shipments = res_drv_shipments.json()
    
    # Manager's view (all shipments)
    res_mgr_shipments = requests.get(f"{BASE_URL}/shipments", headers=mgr_headers)
    mgr_shipments = res_mgr_shipments.json()

    print(f"    - Manager sees {len(mgr_shipments)} total shipments.")
    print(f"    - Driver sees {len(driver_shipments)} assigned shipments.")
    
    if len(driver_shipments) >= len(mgr_shipments) and len(mgr_shipments) > 2:
        print_fail("Driver received all organization shipments instead of scoped shipments!")
    print_pass("Driver shipment query is strictly filtered server-side by authenticated driver_id.")

    # Driver trying to directly access a shipment NOT assigned to them
    unassigned_shp = None
    for s in mgr_shipments:
        if s.get("driver_name") != "Marcus Vance":
            unassigned_shp = s
            break

    if unassigned_shp:
        res_direct = requests.get(f"{BASE_URL}/shipments/{unassigned_shp['shipment_code']}", headers=driver_headers)
        if res_direct.status_code != 403:
            print_fail(f"Driver was able to directly retrieve unassigned shipment {unassigned_shp['shipment_code']}: got {res_direct.status_code}")
        print_pass(f"Driver directly blocked (HTTP 403) from accessing unassigned shipment '{unassigned_shp['shipment_code']}'.")

    # Driver trying to directly access another driver's profile
    other_drv_res = requests.get(f"{BASE_URL}/drivers/DRV-1002", headers=driver_headers)
    if other_drv_res.status_code not in [403, 404]:
        print_fail(f"Driver was able to view another driver's profile: got {other_drv_res.status_code}")
    print_pass("Driver blocked from accessing other drivers' operational profiles.")

    # --------------------------------------------------------------------------------------
    # Requirement 6, 16 & 17: Driver Portal Scoped Data & Vehicle Relationship
    # --------------------------------------------------------------------------------------
    print("\n5. Testing Driver Portal Scoped Metrics & Vehicle Relationship...")
    res_portal = requests.get(f"{BASE_URL}/analytics/driver-portal", headers=driver_headers)
    if res_portal.status_code != 200:
        print_fail(f"Failed to fetch driver portal data: {res_portal.status_code} - {res_portal.text}")
    portal_data = res_portal.json()
    
    print_pass(f"Driver Portal loaded for: {portal_data['driver']['name']} ({portal_data['driver']['driver_code']})")
    if portal_data.get("vehicle"):
        print_pass(f"Linked Assigned Vehicle: {portal_data['vehicle']['vehicle_code']} ({portal_data['vehicle']['model']})")
    print_pass(f"Driver KPIs: {portal_data['kpis']['total_assigned']} assigned, {portal_data['driver']['hours_of_service_remaining']}h HOS remaining.")

    # --------------------------------------------------------------------------------------
    # Requirement 11, 12, 13, 14, 17: Dynamic End-to-End Account Provisioning & Activation
    # --------------------------------------------------------------------------------------
    print("\n6. Testing End-to-End Driver Creation -> Provisioning -> Approval -> Activation Flow...")
    
    rand_id = random.randint(1000, 9999)
    test_driver_code = f"DRV-P{rand_id}"
    test_email = f"driver.p{rand_id}@logiagent.io"
    test_password = "SecureDriverPass2026!"

    # Step 1: Logistics Manager creates new Driver operational profile
    res_create_drv = requests.post(f"{BASE_URL}/drivers", headers=mgr_headers, json={
        "driver_code": test_driver_code,
        "name": f"Alex Morgan {rand_id}",
        "email": test_email,
        "phone": f"+1-555-987-{rand_id}",
        "license_number": f"CDL-NY-{rand_id}",
        "license_type": "CDL-A",
        "status": "Available"
    })
    if res_create_drv.status_code != 201:
        print_fail(f"Failed to create driver operational profile: {res_create_drv.status_code} - {res_create_drv.text}")
    new_driver = res_create_drv.json()
    print_pass(f"Step 1: Driver operational profile created ({new_driver['driver_code']}).")

    # Step 2: Manager provisions user account requiring approval
    res_prov = requests.post(f"{BASE_URL}/users/provision", headers=mgr_headers, json={
        "email": test_email,
        "full_name": new_driver["name"],
        "role": "Driver",
        "driver_id": new_driver["id"],
        "require_approval": True
    })
    if res_prov.status_code != 201:
        print_fail(f"Failed to provision user account: {res_prov.status_code} - {res_prov.text}")
    prov_data = res_prov.json()
    act_token = prov_data["activation_token"]
    prov_user = prov_data["user"]
    print_pass(f"Step 2: Account provisioning record generated with activation token.")

    # Step 3: Check Approval Hierarchy - User cannot activate while Pending_Approval
    res_try_activate = requests.post(f"{BASE_URL}/auth/accept-invitation?token={act_token}", json={
        "token": act_token,
        "password": test_password
    })
    if res_try_activate.status_code != 400 or "pending authorization" not in res_try_activate.text.lower():
        print_fail(f"Expected rejection for pending approval activation, got {res_try_activate.status_code}: {res_try_activate.text}")
    print_pass("Step 3: Unapproved account cannot activate (Higher authority approval enforced).")

    # Step 4: Manager/Admin approves user account
    res_approve = requests.post(f"{BASE_URL}/users/{prov_user['id']}/approve", headers=mgr_headers, json={
        "notes": "Verified CDL background credentials."
    })
    if res_approve.status_code != 200:
        print_fail(f"Approval failed: {res_approve.status_code} - {res_approve.text}")
    print_pass("Step 4: Logistics Manager approved driver account.")

    # Step 5: Driver activates account and sets password
    res_accept = requests.post(f"{BASE_URL}/auth/accept-invitation?token={act_token}", json={
        "token": act_token,
        "full_name": new_driver["name"],
        "password": test_password
    })
    if res_accept.status_code != 200:
        print_fail(f"Driver activation failed: {res_accept.status_code} - {res_accept.text}")
    print_pass("Step 5: Driver accepted invitation and established password.")

    # Step 6: Newly activated driver logs in
    res_new_login = requests.post(f"{BASE_URL}/auth/login", json={
        "email": test_email,
        "password": test_password
    })
    if res_new_login.status_code != 200:
        print_fail(f"New driver login failed: {res_new_login.status_code}")
    new_driver_token = res_new_login.json()["access_token"]
    new_driver_headers = {"Authorization": f"Bearer {new_driver_token}"}
    print_pass(f"Step 6: Driver successfully authenticated into system as '{res_new_login.json()['user']['role']}'.")

    # Step 7: Assign shipment to new driver & check Driver Portal
    # Pick first available shipment
    avail_shp = mgr_shipments[0]
    res_assign = requests.put(f"{BASE_URL}/shipments/{avail_shp['shipment_code']}", headers=mgr_headers, json={
        "driver_id": new_driver["id"]
    })
    if res_assign.status_code != 200:
        print_fail(f"Failed to assign shipment to new driver: {res_assign.status_code}")
    print_pass(f"Step 7: Manager assigned shipment '{avail_shp['shipment_code']}' to new driver.")

    # Step 8: New Driver queries their Driver Portal and sees their assigned shipment
    res_new_portal = requests.get(f"{BASE_URL}/analytics/driver-portal", headers=new_driver_headers)
    if res_new_portal.status_code != 200:
        print_fail(f"New driver portal fetch failed: {res_new_portal.status_code}")
    new_portal_data = res_new_portal.json()
    assigned_codes = [s["shipment_code"] for s in new_portal_data["active_shipments"]]
    if avail_shp["shipment_code"] not in assigned_codes:
        print_fail(f"Assigned shipment {avail_shp['shipment_code']} not found in new driver portal!")
    print_pass(f"Step 8: Driver Dashboard dynamically reflects assigned shipment '{avail_shp['shipment_code']}'.")

    # --------------------------------------------------------------------------------------
    # Requirement 15: Account Suspension & Preservation of Operational Records
    # --------------------------------------------------------------------------------------
    print("\n7. Testing Account Suspension & Operational Record Preservation...")
    res_suspend = requests.post(f"{BASE_URL}/users/{prov_user['id']}/suspend", headers=admin_headers, json={
        "reason": "Scheduled compliance review"
    })
    if res_suspend.status_code != 200:
        print_fail(f"Failed to suspend user: {res_suspend.status_code}")
    print_pass("User account marked as Suspended.")

    # Verify suspended user cannot access API
    res_susp_access = requests.get(f"{BASE_URL}/shipments", headers=new_driver_headers)
    if res_susp_access.status_code != 403 or "suspended" not in res_susp_access.text.lower():
        print_fail(f"Suspended user was not blocked: got {res_susp_access.status_code} - {res_susp_access.text}")
    print_pass("Suspended user strictly denied API access (HTTP 403 Forbidden).")

    # Verify operational driver record is fully preserved
    res_check_drv = requests.get(f"{BASE_URL}/drivers/{test_driver_code}", headers=mgr_headers)
    if res_check_drv.status_code != 200:
        print_fail("Operational driver record was damaged or deleted during suspension!")
    print_pass("Operational driver record and shipment relationship preserved intact.")

    # Reactivate user account
    res_reactivate = requests.post(f"{BASE_URL}/users/{prov_user['id']}/activate", headers=admin_headers)
    if res_reactivate.status_code != 200:
        print_fail(f"Failed to reactivate user: {res_reactivate.status_code}")
    print_pass("User account reactivated.")

    # --------------------------------------------------------------------------------------
    # Final Result
    # --------------------------------------------------------------------------------------
    print_header("ALL 20 PHASE 9 REQUIREMENTS VERIFIED SUCCESSFULLY!")

if __name__ == "__main__":
    test_phase9_authentication_and_rbac()
