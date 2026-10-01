import requests
import json
import random
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

API_BASE = "http://127.0.0.1:8000/api/v1"

session = requests.Session()
login_res = session.post(f"{API_BASE}/auth/login", json={"email": "manager@logiagent.io", "password": "LogiAgent2026!"})
if login_res.status_code == 200:
    session.headers.update({"Authorization": f"Bearer {login_res.json()['access_token']}"})

def run_phase7_tests():
    print("=" * 80)
    print("LOGIAGENT PHASE 7: DYNAMIC DRIVER MANAGEMENT TEST SUITE")
    print("=" * 80)

    # 1. Baseline Stats & Roster
    print("\n[TEST 1] Querying live driver resources and baseline KPIs from Supabase...")
    stats_resp = session.get(f"{API_BASE}/drivers/stats")
    if stats_resp.status_code != 200:
        print(f"FAILED: /drivers/stats returned {stats_resp.status_code}: {stats_resp.text}")
        sys.exit(1)
    stats_before = stats_resp.json()
    total_before = stats_before["total_drivers"]
    available_before = stats_before["available_drivers"]
    print(f" -> Initial Total Drivers: {total_before}")
    print(f" -> Initial Available: {available_before} | Assigned: {stats_before['assigned_drivers']} | On Duty: {stats_before['on_duty_drivers']}")
    print(f" -> Average HOS Remaining: {stats_before['average_hos_remaining']}h | Average Rating: {stats_before['average_rating']}")

    # Query vehicles to get a test vehicle for assignment
    v_resp = session.get(f"{API_BASE}/vehicles")
    all_vehicles = v_resp.json() if v_resp.status_code == 200 else []
    target_vehicle = next((v for v in all_vehicles if v.get("status") in ["Available", "Assigned"]), None)
    if not target_vehicle and all_vehicles:
        target_vehicle = all_vehicles[0]
    print(f" -> Selected Fleet Truck for Testing: {target_vehicle['vehicle_code'] if target_vehicle else 'None'}")

    # 2. Driver Creation
    test_code = f"DRV-D{random.randint(7000, 9999)}"
    test_lic = f"CDL-TX-{random.randint(100000, 999999)}"
    print(f"\n[TEST 2] Testing Dynamic Driver Creation (POST /api/v1/drivers) for {test_code}...")
    create_payload = {
        "driver_code": test_code,
        "name": "Evelyn Harper",
        "email": f"evelyn.harper.{random.randint(100,999)}@logiagent.io",
        "phone": "+1 (555) 789-0123",
        "license_number": test_lic,
        "license_type": "CDL-A",
        "status": "Available",
        "rating": 4.95,
        "hours_of_service_remaining": 10.5,
        "current_vehicle_id": None
    }

    create_resp = session.post(f"{API_BASE}/drivers", json=create_payload)
    if create_resp.status_code != 201:
        print(f"FAILED to create driver: {create_resp.status_code} {create_resp.text}")
        sys.exit(1)

    created_driver = create_resp.json()
    driver_id = created_driver["id"]
    print(f" -> [OK] Created Driver: {created_driver['name']} ({test_code}, ID: {driver_id}) in Supabase")
    print(f" -> License: {created_driver['license_type']} ({created_driver['license_number']}) | HOS: {created_driver['hours_of_service_remaining']}h")

    stats_after_create = session.get(f"{API_BASE}/drivers/stats").json()
    total_after_create = stats_after_create["total_drivers"]
    print(f" -> Driver Count Incremented: {total_before} -> {total_after_create}")
    assert total_after_create == total_before + 1, "Stats total_drivers did not increment correctly"

    # 3. Search and Filtering
    print(f"\n[TEST 3] Testing Driver Search and Filter Capabilities...")
    # Exact search
    search_code_resp = session.get(f"{API_BASE}/drivers", params={"search": test_code})
    search_code_data = search_code_resp.json()
    assert any(d["driver_code"] == test_code for d in search_code_data), f"Driver {test_code} not found by code search"
    print(f" -> [OK] Code search matched: {test_code}")

    # Name search
    search_name_resp = session.get(f"{API_BASE}/drivers", params={"search": "Evelyn"})
    search_name_data = search_name_resp.json()
    assert any(d["driver_code"] == test_code for d in search_name_data), f"Driver {test_code} not found by name search"
    print(f" -> [OK] Name search 'Evelyn' matched {len(search_name_data)} driver(s)")

    # License type filter
    filter_lic_resp = session.get(f"{API_BASE}/drivers", params={"license_type": "CDL-A"})
    filter_lic_data = filter_lic_resp.json()
    assert len(filter_lic_data) > 0, "No CDL-A drivers found"
    print(f" -> [OK] Filter by license_type=CDL-A returned {len(filter_lic_data)} driver(s)")

    # 4. Operational Detailed Inspection
    print(f"\n[TEST 4] Testing Operational Detailed Inspection (GET /api/v1/drivers/{test_code})...")
    detail_resp = session.get(f"{API_BASE}/drivers/{test_code}")
    if detail_resp.status_code != 200:
        print(f"FAILED: /drivers/{test_code} returned {detail_resp.status_code}")
        sys.exit(1)
    detail = detail_resp.json()
    print(f" -> [OK] Driver Details: HOS Remaining: {detail['hours_of_service_remaining']}h ({detail['hos_compliance_status']}), Rating: {detail['rating']}")
    print(f" -> Completed Deliveries: {detail['completed_deliveries_count']} | Active: {detail['active_deliveries_count']}")

    # 5. Driver Update & Vehicle Assignment Synchronization
    print(f"\n[TEST 5] Testing Driver Update & Bidirectional Vehicle Synchronization...")
    update_payload = {
        "rating": 5.0,
        "hours_of_service_remaining": 9.5,
        "phone": "+1 (555) 999-8888",
        "current_vehicle_id": target_vehicle["id"] if target_vehicle else None
    }
    update_resp = session.put(f"{API_BASE}/drivers/{test_code}", json=update_payload)
    if update_resp.status_code != 200:
        print(f"FAILED: update driver returned {update_resp.status_code}: {update_resp.text}")
        sys.exit(1)
    updated = update_resp.json()
    print(f" -> [OK] Updated Driver Phone: {updated['phone']} | Rating: {updated['rating']}")
    if target_vehicle:
        print(f" -> [OK] Assigned Vehicle: {updated.get('assigned_vehicle_code')} (Model: {updated.get('assigned_vehicle_model')})")
        # Verify vehicle table in Supabase now points to driver
        v_check = session.get(f"{API_BASE}/vehicles/{target_vehicle['vehicle_code']}").json()
        assert v_check.get("driver_id") == driver_id, f"Vehicle driver_id not synchronized to {driver_id}"
        print(f" -> [OK] Bidirectional Sync Verified: Vehicle {target_vehicle['vehicle_code']} now reflects driver_id={driver_id}")

    # 6. Active Shipment Linking & Deactivation Protection
    print(f"\n[TEST 6] Testing Active Shipment Integration & Deactivation Protection...")
    # Fetch customer and locations
    cust_resp = session.get(f"{API_BASE}/shipments/meta/customers")
    customers = cust_resp.json() if cust_resp.status_code == 200 else []
    cust_id = customers[0]["id"] if customers else 1

    locs_resp = session.get(f"{API_BASE}/routes/locations")
    locations = locs_resp.json() if locs_resp.status_code == 200 else []
    orig_id = locations[0]["id"] if len(locations) > 0 else 1
    dest_id = locations[1]["id"] if len(locations) > 1 else 2

    shp_code = f"SHP-D{random.randint(7000, 9999)}"
    shp_payload = {
        "shipment_code": shp_code,
        "customer_id": cust_id,
        "origin_id": orig_id,
        "destination_id": dest_id,
        "cargo_type": "Certified Electronics",
        "weight_kg": 3800.0,
        "status": "In Transit",
        "driver_id": driver_id,
        "vehicle_id": target_vehicle["id"] if target_vehicle else None,
        "expected_delivery": "2026-09-25T18:00:00Z"
    }

    create_shp = session.post(f"{API_BASE}/shipments", json=shp_payload)
    if create_shp.status_code != 201:
        print(f"FAILED to create test shipment: {create_shp.status_code} {create_shp.text}")
        sys.exit(1)
    print(f" -> [OK] Created Active Shipment {shp_code} linked to Driver {test_code}")

    # Check driver detail now shows active shipment
    driver_detail_with_shp = session.get(f"{API_BASE}/drivers/{test_code}").json()
    assert driver_detail_with_shp.get("active_shipment_code") == shp_code, "Active shipment not linked in driver detail"
    print(f" -> [OK] Driver Telemetry Reflected: Active Shipment: {driver_detail_with_shp.get('active_shipment_code')} (Corridor: {driver_detail_with_shp.get('active_shipment_origin')} -> {driver_detail_with_shp.get('active_shipment_destination')})")

    # Attempt deactivation while carrying active shipment (must fail)
    deact_blocked_resp = session.delete(f"{API_BASE}/drivers/{test_code}")
    assert deact_blocked_resp.status_code == 400, f"Expected 400 but got {deact_blocked_resp.status_code}"
    print(f" -> [OK] Blocked deactivation with active shipment: {deact_blocked_resp.json().get('detail')}")

    # 7. AI Assistant Integration
    print(f"\n[TEST 7] Testing AI Assistant Discovery of Driver {test_code}...")
    ai_query_payload = {
        "message": f"Show details for driver {test_code}",
        "user_role": "Logistics Manager"
    }
    ai_resp = session.post(f"{API_BASE}/agent/chat", json=ai_query_payload)
    if ai_resp.status_code == 200:
        ai_data = ai_resp.json()
        print(f" -> AI Response for '{ai_query_payload['message']}':\n")
        for line in ai_data.get("response", "").split("\n")[:12]:
            print(f"    {line}")
        print()
    else:
        print(f" -> AI Chat query returned {ai_resp.status_code}")

    # 8. Safe Deactivation after Delivery
    print(f"\n[TEST 8] Testing Safe Deactivation after Shipment Delivery...")
    # Deliver the active shipment
    deliver_resp = session.put(f"{API_BASE}/shipments/{shp_code}", json={"status": "Delivered"})
    assert deliver_resp.status_code == 200, "Failed to mark shipment as delivered"
    print(f" -> [OK] Delivered shipment {shp_code}")

    # Now deactivation must succeed
    deact_resp = session.delete(f"{API_BASE}/drivers/{test_code}")
    if deact_resp.status_code != 200:
        print(f"FAILED: /drivers/{test_code} delete returned {deact_resp.status_code}: {deact_resp.text}")
        sys.exit(1)
    deact_data = deact_resp.json()
    assert deact_data.get("driver", {}).get("status") == "Deactivated", "Driver status is not Deactivated"
    print(f" -> [OK] Driver {test_code} successfully deactivated: Status={deact_data['driver']['status']}")

    # 9. Cleanup
    print(f"\n[TEST 9] Cleaning up test records from Supabase database...")
    from app.core.database import SessionLocal
    from app.models.driver import Driver as DriverModel
    from app.models.shipment import Shipment as ShipmentModel, ShipmentStatusHistory
    from app.models.cost import TransportationCost
    from app.models.vehicle import Vehicle as VehicleModel
    db = SessionLocal()
    try:
        shp = db.query(ShipmentModel).filter(ShipmentModel.shipment_code == shp_code).first()
        if shp:
            db.query(ShipmentStatusHistory).filter(ShipmentStatusHistory.shipment_id == shp.id).delete()
            db.query(TransportationCost).filter(TransportationCost.shipment_id == shp.id).delete()
            db.commit()
            db.delete(shp)
            db.commit()
        
        db.query(DriverModel).filter(DriverModel.driver_code == test_code).delete()
        if target_vehicle:
            tv = db.query(VehicleModel).filter(VehicleModel.id == target_vehicle["id"]).first()
            if tv and tv.driver_id == driver_id:
                tv.driver_id = None
                tv.status = "Available"
        db.commit()
        print(f" -> [OK] Cleaned up test records for {test_code} and {shp_code}")
    finally:
        db.close()

    print("\n" + "=" * 80)
    print("ALL PHASE 7 DRIVER MANAGEMENT TESTS PASSED!")
    print("=" * 80)

if __name__ == "__main__":
    run_phase7_tests()
