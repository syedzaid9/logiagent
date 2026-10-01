import sys
import os
import time
from datetime import datetime, timezone, timedelta
import requests

API_BASE = "http://127.0.0.1:8000/api/v1"

session = requests.Session()
login_res = session.post(f"{API_BASE}/auth/login", json={"email": "admin@logiagent.io", "password": "LogiAgent2026!"})
if login_res.status_code == 200:
    token = login_res.json()["access_token"]
    session.headers.update({"Authorization": f"Bearer {token}"})

def print_header(title: str):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80 + "\n")

def run_phase6_tests():
    print_header("LOGIAGENT PHASE 6: DYNAMIC FLEET & VEHICLE MANAGEMENT TEST SUITE")

    # Step 1: Query initial stats and drivers
    print("[TEST 1] Querying live fleet resources and baseline KPIs from Supabase...")
    stats_before = session.get(f"{API_BASE}/vehicles/stats").json()
    vehicles_before = session.get(f"{API_BASE}/vehicles").json()
    drivers = session.get(f"{API_BASE}/drivers").json()
    customers = session.get(f"{API_BASE}/shipments/meta/customers").json()
    locations = session.get(f"{API_BASE}/routes/locations").json()

    print(f" -> Initial Fleet Total: {stats_before['total_vehicles']} vehicles")
    print(f" -> Initial Available: {stats_before['available_vehicles']} | In Transit/Assigned: {stats_before['in_transit_vehicles'] + stats_before['assigned_vehicles']}")
    print(f" -> Available Drivers in Roster: {len(drivers)}")

    assert len(drivers) >= 2, "Need at least 2 drivers for reassignment testing."
    primary_driver = drivers[0]
    secondary_driver = drivers[1]

    # Step 2: Create new vehicle
    suffix = str(int(time.time()))[-4:]
    test_veh_code = f"TRK-F{suffix}"
    print(f"\n[TEST 2] Testing Dynamic Vehicle Creation (POST /api/v1/vehicles) for {test_veh_code}...")

    create_payload = {
        "vehicle_code": test_veh_code,
        "model": "Volvo VNL 860 Autonomous Linehaul",
        "type": "Semi-Truck (Dry Van)",
        "max_capacity_kg": 22500.0,
        "current_load_kg": 0.0,
        "max_volume_m3": 85.0,
        "current_volume_m3": 0.0,
        "status": "Available",
        "current_location": "Chicago Central Superhub, Chicago, IL",
        "latitude": 41.8781,
        "longitude": -87.6298,
        "fuel_level_pct": 100.0,
        "fuel_type": "Diesel",
        "mileage_km": 14200.0,
        "driver_id": primary_driver["id"]
    }

    create_res = session.post(f"{API_BASE}/vehicles", json=create_payload)
    assert create_res.status_code in [200, 201], f"Vehicle creation failed: {create_res.text}"
    created_veh = create_res.json()
    print(f" -> [OK] Created Vehicle: {created_veh['vehicle_code']} (ID: {created_veh['id']}) in Supabase")
    print(f" -> Assigned Driver: {created_veh['driver_name']} | Max Capacity: {created_veh['max_capacity_kg']} kg")

    # Verify KPI update
    stats_after = session.get(f"{API_BASE}/vehicles/stats").json()
    print(f" -> Fleet Count Incremented: {stats_before['total_vehicles']} -> {stats_after['total_vehicles']}")
    assert stats_after["total_vehicles"] == stats_before["total_vehicles"] + 1, "Fleet KPI count must increment automatically."

    # Step 3: Search and Filter
    print(f"\n[TEST 3] Testing Vehicle Search and Filter Capabilities...")
    search_res = session.get(f"{API_BASE}/vehicles", params={"search": test_veh_code}).json()
    assert len(search_res) == 1, f"Search by vehicle code '{test_veh_code}' failed."
    assert search_res[0]["vehicle_code"] == test_veh_code
    print(f" -> [OK] Exact code search matched: {search_res[0]['vehicle_code']}")

    model_search = session.get(f"{API_BASE}/vehicles", params={"search": "Volvo VNL"}).json()
    assert any(v["vehicle_code"] == test_veh_code for v in model_search), "Model search failed to find vehicle."
    print(f" -> [OK] Model search 'Volvo VNL' matched {len(model_search)} vehicles including {test_veh_code}")

    type_filter = session.get(f"{API_BASE}/vehicles", params={"vehicle_type": "Semi-Truck"}).json()
    assert any(v["vehicle_code"] == test_veh_code for v in type_filter), "Class filter failed."
    print(f" -> [OK] Type filter matched {len(type_filter)} Semi-Truck units.")

    # Step 4: Detailed Operational Telemetry Inspection
    print(f"\n[TEST 4] Testing Vehicle Detailed Operational Inspection (GET /api/v1/vehicles/{test_veh_code})...")
    detail_res = session.get(f"{API_BASE}/vehicles/{test_veh_code}").json()
    assert detail_res["vehicle_code"] == test_veh_code
    assert detail_res["driver_name"] == primary_driver["name"]
    assert detail_res["available_capacity_kg"] == 22500.0
    assert detail_res["utilization_pct"] == 0.0
    print(f" -> [OK] Verified full schema: Available Capacity: {detail_res['available_capacity_kg']} kg, Driver: {detail_res['driver_name']}, Location: {detail_res['current_location']}")

    # Step 5: Vehicle Update & Driver Reassignment
    print(f"\n[TEST 5] Testing Vehicle Update (PUT /api/v1/vehicles/{test_veh_code})...")
    update_payload = {
        "model": "Volvo VNL 860 Max Haul Edition",
        "fuel_level_pct": 88.5,
        "mileage_km": 15800.0,
        "current_location": "Dallas-Fort Worth Gateway, Dallas, TX",
        "latitude": 32.7767,
        "longitude": -96.7970,
        "driver_id": secondary_driver["id"]
    }
    update_res = session.put(f"{API_BASE}/vehicles/{test_veh_code}", json=update_payload)
    assert update_res.status_code == 200, f"Vehicle update failed: {update_res.text}"
    updated_veh = update_res.json()
    assert updated_veh["model"] == "Volvo VNL 860 Max Haul Edition"
    assert updated_veh["driver_name"] == secondary_driver["name"]
    assert updated_veh["current_location"] == "Dallas-Fort Worth Gateway, Dallas, TX"
    print(f" -> [OK] Updated Make/Model: {updated_veh['model']}")
    print(f" -> [OK] Reassigned Driver: {primary_driver['name']} -> {secondary_driver['name']}")
    print(f" -> [OK] Updated Location: {updated_veh['current_location']}")

    # Step 6: Payload Capacity Validation & Active Shipment Linking
    print(f"\n[TEST 6] Testing Payload Capacity Validation & Shipment Integration...")
    now = datetime.now(timezone.utc)
    chicago = locations[0]
    dallas = locations[1]
    
    # Attempt 1: Over-capacity cargo (25,000 kg vs 22,500 kg max)
    overweight_code = f"SHP-X{suffix}"
    overweight_payload = {
        "shipment_code": overweight_code,
        "customer_id": customers[0]["id"],
        "origin_id": chicago["id"],
        "destination_id": dallas["id"],
        "vehicle_id": created_veh["id"],
        "driver_id": secondary_driver["id"],
        "cargo_type": "Dense Steel Coils",
        "weight_kg": 25000.0, # EXCEEDS 22,500 kg max
        "expected_delivery": (now + timedelta(days=2)).isoformat(),
    }
    overweight_res = session.post(f"{API_BASE}/shipments", json=overweight_payload)
    assert overweight_res.status_code == 400, "Backend must reject overweight cargo exceeding vehicle capacity."
    print(f" -> [OK] Successfully blocked overweight shipment (25,000 kg > 22,500 kg max): {overweight_res.json()['detail']}")

    # Attempt 2: Valid payload cargo (4,500 kg)
    valid_shp_code = f"SHP-V{suffix}"
    valid_payload = {
        "shipment_code": valid_shp_code,
        "customer_id": customers[0]["id"],
        "origin_id": chicago["id"],
        "destination_id": dallas["id"],
        "vehicle_id": created_veh["id"],
        "driver_id": secondary_driver["id"],
        "cargo_type": "Precision Electronics",
        "weight_kg": 4500.0,
        "expected_delivery": (now + timedelta(days=2)).isoformat(),
        "status": "In Transit"
    }
    valid_res = session.post(f"{API_BASE}/shipments", json=valid_payload)
    assert valid_res.status_code in [200, 201], f"Shipment creation failed: {valid_res.text}"
    print(f" -> [OK] Created valid shipment {valid_shp_code} (4,500 kg) linked to {test_veh_code}")

    # Verify vehicle details now dynamically link the active shipment
    veh_with_shipment = session.get(f"{API_BASE}/vehicles/{test_veh_code}").json()
    assert veh_with_shipment["active_shipment_code"] == valid_shp_code
    assert veh_with_shipment["current_load_kg"] == 4500.0
    assert veh_with_shipment["available_capacity_kg"] == 18000.0
    assert veh_with_shipment["utilization_pct"] == 20.0
    print(f" -> [OK] Vehicle {test_veh_code} telemetry synced: Active Shipment: {veh_with_shipment['active_shipment_code']}, Utilization: {veh_with_shipment['utilization_pct']}%, Free: {veh_with_shipment['available_capacity_kg']} kg")

    # Step 7: AI Assistant Fleet Discovery
    print(f"\n[TEST 7] Testing AI Assistant Discovery of {test_veh_code}...")
    ai_q1 = f"Which vehicle is available for 15000 kg payload?"
    ai_resp1 = session.post(f"{API_BASE}/agent/query", json={"message": ai_q1, "user_role": "Logistics Manager"}).json().get("response", "")
    print(f" -> AI Response for '{ai_q1}':\n")
    for line in ai_resp1.split("\n")[:8]:
        try:
            print(f"    {line}")
        except Exception:
            print(f"    {line.encode('ascii', 'replace').decode('ascii')}")
    assert test_veh_code in ai_resp1 or "Available Fleet Capacity" in ai_resp1, "AI Assistant must discover vehicle fleet records."

    # Step 8: Deactivation & Active-Shipment Protection
    print(f"\n[TEST 8] Testing Deactivation & Active-Shipment Protection...")
    # Attempt deactivation while assigned to active shipment
    deact_blocked = session.delete(f"{API_BASE}/vehicles/{test_veh_code}")
    assert deact_blocked.status_code == 400, "Must block deactivation of vehicle with active shipment."
    print(f" -> [OK] Blocked deactivation with active shipment: {deact_blocked.json()['detail']}")

    # Deliver the active shipment
    session.put(f"{API_BASE}/shipments/{valid_shp_code}", json={"status": "Delivered"})
    print(f" -> [OK] Delivered active shipment {valid_shp_code}, releasing vehicle capacity.")

    # Now deactivate vehicle
    deact_res = session.delete(f"{API_BASE}/vehicles/{test_veh_code}")
    assert deact_res.status_code == 200, f"Deactivation failed: {deact_res.text}"
    deactivated_v = deact_res.json()["vehicle"]
    assert deactivated_v["status"] == "Deactivated"
    print(f" -> [OK] Successfully deactivated vehicle {test_veh_code} (Status: {deactivated_v['status']})")

    # Step 9: Clean up test records
    print(f"\n[TEST 9] Cleaning up test records from Supabase database...")
    from app.core.database import SessionLocal
    from app.models.vehicle import Vehicle
    from app.models.shipment import Shipment, ShipmentStatusHistory
    from app.models.cost import TransportationCost
    
    db = SessionLocal()
    try:
        shp = db.query(Shipment).filter(Shipment.shipment_code == valid_shp_code).first()
        if shp:
            db.query(ShipmentStatusHistory).filter(ShipmentStatusHistory.shipment_id == shp.id).delete()
            db.query(TransportationCost).filter(TransportationCost.shipment_id == shp.id).delete()
            db.delete(shp)
        
        veh = db.query(Vehicle).filter(Vehicle.vehicle_code == test_veh_code).first()
        if veh:
            db.delete(veh)
            
        db.commit()
        print(f" -> [OK] Cleaned up test vehicle {test_veh_code} and shipment {valid_shp_code}")
    finally:
        db.close()

    print_header("ALL PHASE 6 FLEET & VEHICLE MANAGEMENT TESTS PASSED!")

if __name__ == "__main__":
    run_phase6_tests()
