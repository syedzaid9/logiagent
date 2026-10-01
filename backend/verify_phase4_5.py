import sys
import os
import json
import urllib.request
import urllib.error
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.core.database import SessionLocal
from app.models.vehicle import Vehicle
from app.models.driver import Driver
from app.models.shipment import Shipment

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_URL = "http://127.0.0.1:8000/api/v1"

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

def log(msg):
    print(msg, flush=True)

def main():
    log("=" * 80)
    log("LOGIAGENT PHASE 4.5: DYNAMIC DATA INTEGRITY & CREATION SUITE")
    log("=" * 80)

    # 1. Test Analytics Dashboard Dynamic Values
    log("\n[TEST 1] Testing Analytics Dashboard Dynamic Telemetry...")
    dashboard = api_call("/analytics/dashboard")
    kpis = dashboard["kpis"]
    log(f" -> Total Shipments: {kpis['total_shipments']}")
    log(f" -> Today's Deliveries Count (Dynamic): {kpis['today_deliveries_count']}")
    log(f" -> Average ETA Hours (Dynamic): {kpis['average_eta_hours']}")
    log(f" -> Total Transportation Cost: ${kpis['total_transportation_cost']}")
    log(f" -> On-Time Rate: {kpis['on_time_delivery_rate_pct']}%")
    log(f" -> Delay Root Causes ({len(dashboard['delay_root_causes'])}):")
    for d in dashboard["delay_root_causes"]:
        log(f"     * {d['reason']}: {d['count']} shipments ({d['percentage']}%)")
    
    assert isinstance(kpis["today_deliveries_count"], int)
    assert isinstance(kpis["average_eta_hours"], (int, float))
    assert isinstance(dashboard["delay_root_causes"], list)

    log(f" -> Recent Activity (Sample Time-Ago):")
    for act in dashboard["recent_activity"][:3]:
        log(f"     * [{act['status']}] @ {act['location']}: {act['time_ago']}")

    # 2. Test Vehicle Creation (POST /api/v1/vehicles)
    log("\n[TEST 2] Testing Dynamic Vehicle Creation (POST /api/v1/vehicles)...")
    test_veh_code = f"TRK-T{int(datetime.now().timestamp()) % 1000}"
    veh_payload = {
        "vehicle_code": test_veh_code,
        "model": "Volvo VNL 860 Autonomous Test",
        "type": "Semi-Truck (Dry Van)",
        "max_capacity_kg": 22000.0,
        "max_volume_m3": 85.0,
        "fuel_type": "Diesel",
        "current_location": "LogiAgent Innovation Center, Chicago, IL",
        "latitude": 41.8818,
        "longitude": -87.6231,
        "fuel_level_pct": 100.0,
        "mileage_km": 500.0
    }
    created_veh = api_call("/vehicles", method="POST", data=veh_payload)
    assert created_veh["vehicle_code"] == test_veh_code
    log(f" -> Successfully created Vehicle: {created_veh['vehicle_code']} (ID: {created_veh['id']}) in Supabase")

    # Verify Vehicle in GET /vehicles
    all_vehicles = api_call("/vehicles")
    veh_match = next((v for v in all_vehicles if v["vehicle_code"] == test_veh_code), None)
    assert veh_match is not None
    log(f" -> Verified {test_veh_code} exists in live fleet listing (Total Vehicles: {len(all_vehicles)})")

    # 3. Test Driver Creation (POST /api/v1/drivers)
    log("\n[TEST 3] Testing Dynamic Driver Creation (POST /api/v1/drivers)...")
    test_drv_code = f"DRV-T{int(datetime.now().timestamp()) % 1000}"
    drv_payload = {
        "driver_code": test_drv_code,
        "name": "Alexandria Chen",
        "email": f"alex.chen.{test_drv_code.lower()}@logiagent.io",
        "phone": "+1 (555) 892-4411",
        "license_number": f"CDL-TX-{test_drv_code}",
        "license_type": "CDL-A",
        "status": "Available",
        "rating": 4.95,
        "hours_of_service_remaining": 11.0,
        "current_vehicle_id": created_veh["id"]
    }
    created_drv = api_call("/drivers", method="POST", data=drv_payload)
    assert created_drv["driver_code"] == test_drv_code
    log(f" -> Successfully created Driver: {created_drv['name']} ({created_drv['driver_code']}) in Supabase")

    # Verify Driver in GET /drivers
    all_drivers = api_call("/drivers")
    drv_match = next((d for d in all_drivers if d["driver_code"] == test_drv_code), None)
    assert drv_match is not None
    log(f" -> Verified {test_drv_code} exists in live driver roster (Total Drivers: {len(all_drivers)})")

    # 4. Test AI Assistant Discovery of New Vehicle & Driver
    log("\n[TEST 4] Testing AI Assistant Discovery of Newly Created Entities...")
    ai_veh_query = api_call("/agent/chat", method="POST", data={
        "message": f"Which vehicle is available for a 21000 kg shipment?",
        "user_role": "Logistics Manager"
    })
    log(f" -> AI Response for high payload capacity:")
    log(f"    {ai_veh_query['response'][:200]}...")
    assert len(ai_veh_query.get("tools_used", [])) > 0

    ai_drv_query = api_call("/agent/chat", method="POST", data={
        "message": f"Show me the available drivers.",
        "user_role": "Logistics Manager"
    })
    log(f" -> AI Response for available drivers:")
    log(f"    {ai_drv_query['response'][:200]}...")

    # 5. Clean Up Test Records from Supabase DB
    log("\n[TEST 5] Cleaning up test records from database...")
    db = SessionLocal()
    try:
        db.query(Driver).filter(Driver.driver_code == test_drv_code).delete()
        db.query(Vehicle).filter(Vehicle.vehicle_code == test_veh_code).delete()
        db.commit()
        log(f" -> Cleaned up test records: {test_veh_code} and {test_drv_code}")
    finally:
        db.close()

    # 6. Test RAG Policy Documents List
    log("\n[TEST 6] Testing RAG Policy Explorer Documents API (/api/v1/rag/documents)...")
    docs_resp = api_call("/rag/documents")
    log(f" -> Retrieved {len(docs_resp)} documents from Supabase:")
    for d in docs_resp[:3]:
        log(f"     * '{d['document_name']}' - Title: '{d['title']}', Chunks: {d['total_chunks']}, Pages: {d['total_pages']}")
    assert len(docs_resp) > 0
    assert "total_chunks" in docs_resp[0]
    assert "document_name" in docs_resp[0]

    log("\n" + "=" * 80)
    log("🎉 ALL PHASE 4.5 DYNAMIC DATA INTEGRITY & CREATION TESTS PASSED! 🎉")
    log("=" * 80)

if __name__ == "__main__":
    main()
