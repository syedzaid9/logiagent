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

def run_phase5_1_tests():
    print_header("LOGIAGENT PHASE 5.1: SHIPMENT DATA CONSISTENCY & DISTANCE VERIFICATION SUITE")

    # Step 1: Query resources
    print("[TEST 1] Fetching live system resources from Supabase...")
    customers = session.get(f"{API_BASE}/shipments/meta/customers").json()
    locations = session.get(f"{API_BASE}/routes/locations").json()
    vehicles = session.get(f"{API_BASE}/vehicles").json()
    drivers = session.get(f"{API_BASE}/drivers").json()

    assert len(customers) > 0, "No customers found in database."
    assert len(locations) >= 2, "Insufficient delivery locations in database."
    assert len(vehicles) > 0, "No vehicles found in database."
    assert len(drivers) > 0, "No drivers found in database."

    # Origin: Chicago, Destination: Dallas
    chicago = next((l for l in locations if "chicago" in l["city"].lower()), locations[0])
    dallas = next((l for l in locations if "dallas" in l["city"].lower()), locations[1])
    test_cust = customers[0]
    test_veh = vehicles[0]
    test_drv = drivers[0]

    print(f" -> Origin: {chicago['name']} ({chicago['city']}, {chicago['state']})")
    print(f" -> Destination: {dallas['name']} ({dallas['city']}, {dallas['state']})")
    print(f" -> Customer: {test_cust['name']} | Fleet: {test_veh['vehicle_code']} | Driver: {test_drv['name']}")

    # Step 2: Create new shipment
    suffix = str(int(time.time()))[-4:]
    test_code = f"SHP-C{suffix}"
    print(f"\n[TEST 2] Creating test shipment {test_code} (POST /api/v1/shipments)...")

    now = datetime.now(timezone.utc)
    create_payload = {
        "shipment_code": test_code,
        "customer_id": test_cust["id"],
        "origin_id": chicago["id"],
        "destination_id": dallas["id"],
        "vehicle_id": test_veh["id"],
        "driver_id": test_drv["id"],
        "cargo_type": "Precision Medical Equipment",
        "weight_kg": 3200.0,
        "volume_m3": 18.5,
        "temperature_controlled": True,
        "target_temp_celsius": 4.0,
        "pickup_time": now.isoformat(),
        "expected_delivery": (now + timedelta(days=2)).isoformat(),
        "special_instructions": "Maintain strict cold chain; Phase 5.1 data consistency test."
    }

    resp = session.post(f"{API_BASE}/shipments", json=create_payload)
    assert resp.status_code in [200, 201], f"Shipment creation failed: {resp.text}"
    created_shp = resp.json()
    print(f" -> Successfully created {test_code} (ID: {created_shp['id']}) in Supabase!")
    
    # Step 3: Check initial distance and cost consistency
    print(f"\n[TEST 3] Testing Canonical Route Distance & Cost Consistency...")
    cost_data = created_shp.get("cost_breakdown", {})
    cost_distance = cost_data.get("distance_km")
    total_cost = created_shp.get("cost_total_usd")
    print(f" -> Created Shipment Transportation Cost: ${total_cost} USD on {cost_distance} km")

    # Route Optimization Distance
    route_res = session.get(f"{API_BASE}/routes/shipment/{test_code}").json()
    route_distance = route_res.get("recommended_route", {}).get("distance_km")
    print(f" -> Route Optimization Recommended Distance: {route_distance} km")

    # Verify distance consistency
    assert cost_distance is not None and route_distance is not None, "Distances must not be null"
    assert abs(cost_distance - route_distance) < 0.1, f"Distance discrepancy detected! Cost distance={cost_distance}, Route distance={route_distance}"
    print(f" -> [OK] PERFECT DISTANCE CONSISTENCY: Both Cost & Route systems use canonical {route_distance} km!")

    # Step 4: Status Transitions (In Transit -> Delayed -> Delivered)
    print(f"\n[TEST 4] Testing Operational Lifecycle Transitions & Delivered Checkpoint Logic...")
    
    # In Transit
    t1 = session.put(f"{API_BASE}/shipments/{test_code}", json={
        "status": "In Transit",
        "current_location_name": "Midwest Intermodal Corridor Gateway",
        "current_latitude": 39.7817,
        "current_longitude": -89.6501,
        "notes": "Departed Chicago superhub on route to Dallas corridor."
    }).json()
    assert t1["status"] == "In Transit"
    print(f" -> Transition 1: [In Transit] @ '{t1['current_location_name']}'")

    # Delayed
    t2 = session.put(f"{API_BASE}/shipments/{test_code}", json={
        "status": "Delayed",
        "current_location_name": "St. Louis Regional Highway Checkpoint",
        "current_latitude": 38.6270,
        "current_longitude": -90.1994,
        "delay_minutes": 55,
        "delay_reason": "Severe Storm & Highway Speed Restriction",
        "notes": "Encountered thunderstorm slowdown; delayed 55 min."
    }).json()
    assert t2["status"] == "Delayed"
    print(f" -> Transition 2: [Delayed] (+55m: '{t2['delay_reason']}') @ '{t2['current_location_name']}'")

    # Delivered
    t3 = session.put(f"{API_BASE}/shipments/{test_code}", json={
        "status": "Delivered",
        "notes": "Arrived at Dallas-Fort Worth Gateway; dock receiving complete."
    }).json()
    assert t3["status"] == "Delivered"
    assert t3.get("actual_delivery") is not None, "actual_delivery timestamp must be populated on delivery"
    print(f" -> Transition 3: [Delivered] Actual Delivery: {t3['actual_delivery']}")
    print(f" -> Location on Delivery: '{t3['current_location_name']}'")
    assert "dallas" in t3["current_location_name"].lower(), f"Current location should be at destination on delivery, got: {t3['current_location_name']}"
    assert t3.get("delay_risk_score") == 0.0, f"Delivered delay risk score should be 0, got {t3.get('delay_risk_score')}"

    # Verify History
    detail_res = session.get(f"{API_BASE}/shipments/{test_code}").json()
    history = detail_res.get("history", [])
    print(f" -> Verified {len(history)} immutable audit checkpoints logged in Supabase.")
    assert len(history) >= 4, f"Expected at least 4 history records, got {len(history)}"
    assert history[0]["status"] == "Delivered", "Latest checkpoint must be Delivered"

    # Step 5: AI Assistant Queries for Delivered Shipment
    print(f"\n[TEST 5] Testing AI Assistant Discovery and Completed-State Telemetry for {test_code}...")
    
    # Query 1: Tracking / Location
    q1 = f"Where is shipment {test_code}?"
    ai1 = session.post(f"{API_BASE}/agent/query", json={"message": q1, "user_role": "Logistics Manager"}).json()
    resp1 = ai1.get("response", "")
    print(f" -> AI Response for '{q1}':\n")
    for line in resp1.split("\n"):
        try:
            print(f"    {line}")
        except Exception:
            print(f"    {line.encode('ascii', 'replace').decode('ascii')}")
    assert "Delivered" in resp1, f"AI must report Delivered status, got: {resp1}"
    assert "Completed" in resp1 or "Delivery Complete" in resp1, f"AI must report delivery completed, got: {resp1}"

    # Query 2: ETA
    q2 = f"What is the ETA for {test_code}?"
    ai2 = session.post(f"{API_BASE}/agent/query", json={"message": q2, "user_role": "Logistics Manager"}).json()
    resp2 = ai2.get("response", "")
    print(f"\n -> AI Response for '{q2}':\n")
    for line in resp2.split("\n"):
        try:
            print(f"    {line}")
        except Exception:
            print(f"    {line.encode('ascii', 'replace').decode('ascii')}")
    assert "Delivered" in resp2, f"AI must report Delivered status on ETA query, got: {resp2}"
    assert "Completed" in resp2 or "No active transit ETA" in resp2 or "N/A" in resp2, f"AI must indicate no active transit ETA applicable, got: {resp2}"

    # Query 3: Cost
    q3 = f"Show transportation cost for {test_code}."
    ai3 = session.post(f"{API_BASE}/agent/query", json={"message": q3, "user_role": "Logistics Manager"}).json()
    resp3 = ai3.get("response", "")
    print(f"\n -> AI Response for '{q3}':\n")
    for line in resp3.split("\n"):
        try:
            print(f"    {line}")
        except Exception:
            print(f"    {line.encode('ascii', 'replace').decode('ascii')}")
    assert f"{route_distance}" in resp3 or f"{cost_distance}" in resp3, "AI must report canonical distance"

    # Step 6: Cleanup test shipment
    print(f"\n[TEST 6] Cleaning up test records from Supabase database...")
    from app.core.database import SessionLocal
    from app.models.shipment import Shipment, ShipmentStatusHistory
    from app.models.cost import TransportationCost
    
    db = SessionLocal()
    try:
        shp = db.query(Shipment).filter(Shipment.shipment_code == test_code).first()
        if shp:
            db.query(ShipmentStatusHistory).filter(ShipmentStatusHistory.shipment_id == shp.id).delete()
            db.query(TransportationCost).filter(TransportationCost.shipment_id == shp.id).delete()
            db.delete(shp)
            db.commit()
            print(f" -> Successfully cleaned up test records for {test_code}")
    finally:
        db.close()

    print_header("ALL PHASE 5.1 CONSISTENCY & DISTANCE VERIFICATION TESTS PASSED!")

if __name__ == "__main__":
    run_phase5_1_tests()
