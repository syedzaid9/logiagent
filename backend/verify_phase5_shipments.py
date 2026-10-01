import sys
import os
import json
import urllib.request
import urllib.error
from datetime import datetime, timedelta

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.core.database import SessionLocal
from app.models.vehicle import Vehicle
from app.models.driver import Driver
from app.models.shipment import Shipment, ShipmentStatusHistory
from app.models.cost import TransportationCost

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_URL = "http://127.0.0.1:8000/api/v1"

def log(msg):
    print(msg, flush=True)

_auth_token = None

def get_auth_token():
    global _auth_token
    if not _auth_token:
        login_req = urllib.request.Request(
            f"{BASE_URL}/auth/login",
            data=json.dumps({"email": "admin@logiagent.io", "password": "LogiAgent2026!"}).encode(),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(login_req) as login_res:
            _auth_token = json.loads(login_res.read())["access_token"]
    return _auth_token

def api_call(endpoint: str, method: str = "GET", data: dict = None):
    url = f"{BASE_URL}{endpoint}"
    token = get_auth_token()
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    req_data = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=req_data, headers=headers, method=method)
    
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

def main():
    log("=" * 80)
    log("LOGIAGENT PHASE 5: DYNAMIC SHIPMENT MANAGEMENT TEST SUITE")
    log("=" * 80)

    # Step 1: Query existing metadata
    log("\n[TEST 1] Fetching live system resources from Supabase...")
    customers = api_call("/shipments/meta/customers")
    locations = api_call("/routes/locations")
    vehicles = api_call("/vehicles")
    drivers = api_call("/drivers")
    
    assert len(customers) > 0, "No customers found in database"
    assert len(locations) > 1, "Insufficient locations found in database"
    assert len(vehicles) > 0, "No vehicles found in database"
    assert len(drivers) > 0, "No drivers found in database"
    
    log(f" -> Found {len(customers)} customers, {len(locations)} hubs, {len(vehicles)} vehicles, {len(drivers)} drivers.")

    # Step 2: Dynamic Shipment Creation (POST /api/v1/shipments)
    log("\n[TEST 2] Testing Dynamic Shipment Creation (POST /api/v1/shipments)...")
    test_code = f"SHP-T{int(datetime.now().timestamp()) % 10000}"
    cust = customers[0]
    orig = locations[0]
    dest = locations[1]
    veh = vehicles[0]
    drv = drivers[0]

    create_payload = {
        "shipment_code": test_code,
        "customer_id": cust["id"],
        "origin_id": orig["id"],
        "destination_id": dest["id"],
        "vehicle_id": veh["id"],
        "driver_id": drv["id"],
        "status": "Assigned",
        "cargo_type": "Precision Medical Diagnostics",
        "weight_kg": 3400.0,
        "volume_m3": 14.5,
        "temperature_controlled": True,
        "target_temp_celsius": 4.0,
        "expected_delivery": (datetime.utcnow() + timedelta(days=2)).isoformat(),
        "special_instructions": "Fragile cold-chain payload. Mandatory dock inspection upon arrival."
    }

    created = api_call("/shipments", method="POST", data=create_payload)
    assert created["shipment_code"] == test_code
    assert created["customer_name"] == cust["name"]
    assert created["origin_city"] == orig["city"]
    assert created["destination_city"] == dest["city"]
    assert created["vehicle_code"] == veh["vehicle_code"]
    assert created["driver_name"] == drv["name"]
    assert created["cost_total_usd"] is not None and created["cost_total_usd"] > 0
    assert len(created.get("history", [])) >= 1
    log(f" -> Successfully created shipment {test_code} (ID: {created['id']}) in Supabase!")
    log(f" -> Auto-generated TransportationCost: ${created['cost_total_usd']} USD")
    log(f" -> Initial Checkpoint: [{created['history'][0]['status']}] @ {created['history'][0]['location_name']}")

    # Step 3: Verify in GET /shipments and GET /shipments/{code}
    log("\n[TEST 3] Testing Listing, Search, and Detailed Inspection...")
    all_shipments = api_call("/shipments")
    match_in_list = next((s for s in all_shipments if s["shipment_code"] == test_code), None)
    assert match_in_list is not None, "Created shipment not in live shipments listing"
    log(f" -> Verified {test_code} appears in live shipment table (Total Shipments: {len(all_shipments)})")

    searched = api_call(f"/shipments?search={test_code}")
    assert len(searched) == 1 and searched[0]["shipment_code"] == test_code
    log(f" -> Verified search query for '{test_code}' returned exact match")

    detail = api_call(f"/shipments/{test_code}")
    assert detail["shipment_code"] == test_code
    assert detail["temperature_controlled"] is True
    assert detail["target_temp_celsius"] == 4.0
    log(f" -> Verified detail endpoint (/api/v1/shipments/{test_code}) returns full schema")

    # Step 4: Test Dynamic Status Transitions & Audit Trail
    log("\n[TEST 4] Testing Lifecycle Status Transitions & Audit Logging (PUT /api/v1/shipments/{code})...")
    
    # 4a: Transition to In Transit
    up1 = api_call(f"/shipments/{test_code}", method="PUT", data={
        "status": "In Transit",
        "current_location_name": f"Interstate Gateway En Route to {dest['city']}",
        "current_latitude": 38.5,
        "current_longitude": -90.2,
        "notes": "Driver departed origin dock after cargo temperature verification."
    })
    assert up1["status"] == "In Transit"
    log(f" -> Checkpoint 1: In Transit recorded at '{up1['current_location_name']}'")

    # 4b: Transition to Delayed
    up2 = api_call(f"/shipments/{test_code}", method="PUT", data={
        "status": "Delayed",
        "delay_minutes": 55,
        "delay_reason": "Severe Storm & Speed Restriction",
        "notes": "Weather radar indicates mandatory 45 mph safety restriction."
    })
    assert up2["status"] == "Delayed"
    assert up2["delay_minutes"] == 55
    log(f" -> Checkpoint 2: Delayed (+55m) recorded with reason '{up2['delay_reason']}'")

    # 4c: Transition to Delivered
    up3 = api_call(f"/shipments/{test_code}", method="PUT", data={
        "status": "Delivered",
        "notes": "Delivered successfully. Consignee signature obtained."
    })
    assert up3["status"] == "Delivered"
    assert up3["actual_delivery"] is not None
    assert len(up3["history"]) >= 4
    log(f" -> Checkpoint 3: Delivered recorded at {up3['actual_delivery']} ({len(up3['history'])} total audit checkpoints)")

    # Step 5: Test AI Assistant Discovery
    log("\n[TEST 5] Testing AI Assistant Discovery of Newly Created Shipment...")
    ai_status_query = api_call("/agent/chat", method="POST", data={
        "message": f"What is the status and destination of shipment {test_code}?",
        "user_role": "Logistics Manager"
    })
    log(f" -> AI Response for status query:")
    log(f"    {ai_status_query['response'][:250]}...")
    assert len(ai_status_query.get("tools_used", [])) > 0

    ai_cost_query = api_call("/agent/chat", method="POST", data={
        "message": f"Show transportation cost for {test_code}.",
        "user_role": "Logistics Manager"
    })
    log(f" -> AI Response for cost query:")
    log(f"    {ai_cost_query['response'][:250]}...")
    assert len(ai_cost_query.get("tools_used", [])) > 0

    # Step 6: Test Dynamic Route Calculation for the New Shipment
    log("\n[TEST 6] Testing Dynamic Route Optimization for Newly Created Shipment...")
    route_resp = api_call(f"/routes/shipment/{test_code}")
    assert route_resp["success"] is True
    assert route_resp["recommended_route"]["distance_km"] > 0
    log(f" -> Route calculated dynamically: Corridor '{route_resp['recommended_route']['corridor']}', Distance: {route_resp['recommended_route']['distance_km']} km, Travel Time: {route_resp['recommended_route']['duration_formatted']}")

    # Step 7: Clean Up Test Records from Supabase DB
    log("\n[TEST 7] Cleaning up test records from Supabase database...")
    db = SessionLocal()
    try:
        db.query(TransportationCost).filter(TransportationCost.shipment_id == created["id"]).delete()
        db.query(ShipmentStatusHistory).filter(ShipmentStatusHistory.shipment_id == created["id"]).delete()
        db.query(Shipment).filter(Shipment.id == created["id"]).delete()
        
        # Reset vehicle and driver statuses if needed
        veh_db = db.query(Vehicle).filter(Vehicle.id == veh["id"]).first()
        if veh_db and veh_db.status == "Assigned":
            veh_db.status = "Available"
        drv_db = db.query(Driver).filter(Driver.id == drv["id"]).first()
        if drv_db and drv_db.status == "Assigned":
            drv_db.status = "Available"

        db.commit()
        log(f" -> Cleaned up test records for {test_code}")
    finally:
        db.close()

    log("\n" + "=" * 80)
    log("🎉 ALL PHASE 5 DYNAMIC SHIPMENT MANAGEMENT TESTS PASSED! 🎉")
    log("=" * 80)

if __name__ == "__main__":
    main()
