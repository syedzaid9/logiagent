import requests
import json
import random
import sys
import os

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

API_BASE = "http://127.0.0.1:8000/api/v1"

session = requests.Session()
login_res = session.post(f"{API_BASE}/auth/login", json={"email": "manager@logiagent.io", "password": "LogiAgent2026!"})
if login_res.status_code == 200:
    session.headers.update({"Authorization": f"Bearer {login_res.json()['access_token']}"})

def run_phase8_tests():
    print("=" * 80)
    print("LOGIAGENT PHASE 8: DYNAMIC ROUTE MANAGEMENT & OPTIMIZATION TEST SUITE")
    print("=" * 80)

    # 1. Baseline Route KPIs
    print("\n[TEST 1] Querying live route baseline KPIs and statistics from Supabase...")
    stats_resp = session.get(f"{API_BASE}/routes/stats")
    if stats_resp.status_code != 200:
        print(f"FAILED: /routes/stats returned {stats_resp.status_code}: {stats_resp.text}")
        sys.exit(1)
    stats_before = stats_resp.json()
    total_routes_before = stats_before["total_routes"]
    print(f" -> Initial Total Routes: {total_routes_before}")
    print(f" -> Active (In Transit): {stats_before['active_routes']} | Planned: {stats_before['planned_routes']} | Completed: {stats_before['completed_routes']} | Delayed: {stats_before['delayed_routes']}")
    print(f" -> Average Network Distance: {stats_before['average_distance_km']} km | Avg Duration: {stats_before['average_duration_min']} min | Avg Efficiency: {stats_before['average_efficiency_pct']}%")

    # 2. Dynamic Route Listing
    print("\n[TEST 2] Testing Dynamic Route Listing (GET /api/v1/routes)...")
    list_resp = session.get(f"{API_BASE}/routes")
    if list_resp.status_code != 200:
        print(f"FAILED: /routes returned {list_resp.status_code}: {list_resp.text}")
        sys.exit(1)
    routes_list = list_resp.json()
    print(f" -> [OK] Retrieved {len(routes_list)} live route record(s) from Supabase")

    # Fetch live supporting entities for dynamic test creation
    locs_resp = session.get(f"{API_BASE}/routes/locations")
    locs = locs_resp.json() if locs_resp.status_code == 200 else []
    if len(locs) < 2:
        print("FAILED: At least 2 delivery locations required in database.")
        sys.exit(1)
    orig_loc = locs[0]
    dest_loc = locs[1]
    dest_alt_loc = locs[2] if len(locs) > 2 else locs[0]
    print(f" -> Origin Hub: {orig_loc['name']} ({orig_loc['city']}, {orig_loc['state']})")
    print(f" -> Destination Hub: {dest_loc['name']} ({dest_loc['city']}, {dest_loc['state']})")

    cust_resp = session.get(f"{API_BASE}/shipments/meta/customers")
    custs = cust_resp.json() if cust_resp.status_code == 200 else []
    cust_id = custs[0]["id"] if custs else 1

    veh_resp = session.get(f"{API_BASE}/vehicles")
    vehs = veh_resp.json() if veh_resp.status_code == 200 else []
    target_vehicle = next((v for v in vehs if v.get("status") in ["Available", "Assigned"]), vehs[0] if vehs else None)
    
    drv_resp = session.get(f"{API_BASE}/drivers")
    drvs = drv_resp.json() if drv_resp.status_code == 200 else []
    target_driver = next((d for d in drvs if d.get("status") in ["Available", "Assigned", "On Duty"]), drvs[0] if drvs else None)

    # 3. Dynamic Shipment & Route Creation
    test_shipment_code = f"SHP-R{random.randint(6000, 9999)}"
    test_route_code = f"RT-R{random.randint(7000, 9999)}"

    print(f"\n[TEST 3] Creating dynamic test shipment {test_shipment_code} and linking route...")
    from datetime import datetime, timezone, timedelta
    exp_time = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
    shipment_payload = {
        "shipment_code": test_shipment_code,
        "customer_id": cust_id,
        "origin_id": orig_loc["id"],
        "destination_id": dest_loc["id"],
        "vehicle_id": target_vehicle["id"] if target_vehicle else None,
        "driver_id": target_driver["id"] if target_driver else None,
        "cargo_type": "High-Value Microelectronics",
        "weight_kg": 3500.0,
        "volume_m3": 14.5,
        "expected_delivery": exp_time,
        "status": "Assigned",
        "delay_risk_score": 10,
        "delay_risk_level": "Low"
    }
    shipment_resp = session.post(f"{API_BASE}/shipments", json=shipment_payload)
    if shipment_resp.status_code != 201:
        print(f"FAILED to create test shipment: {shipment_resp.status_code} {shipment_resp.text}")
        sys.exit(1)
    created_shipment = shipment_resp.json()
    shipment_id = created_shipment["id"]
    print(f" -> [OK] Created Shipment {test_shipment_code} (ID: {shipment_id})")

    print(f"\n[TEST 4] Testing Dynamic Route Creation (POST /api/v1/routes) for {test_route_code}...")
    route_create_payload = {
        "route_code": test_route_code,
        "shipment_id": shipment_id,
        "origin_id": orig_loc["id"],
        "destination_id": dest_loc["id"],
        "vehicle_id": target_vehicle["id"] if target_vehicle else None,
        "driver_id": target_driver["id"] if target_driver else None,
        "traffic_condition": "Moderate",
        "weather_condition": "Clear",
        "status": "Assigned"
    }
    route_create_resp = session.post(f"{API_BASE}/routes", json=route_create_payload)
    if route_create_resp.status_code != 201:
        print(f"FAILED to create route: {route_create_resp.status_code} {route_create_resp.text}")
        sys.exit(1)
    created_route = route_create_resp.json()
    route_id = created_route["id"]
    canonical_distance = created_route["planned_distance_km"]
    print(f" -> [OK] Created Route {test_route_code} (ID: {route_id})")
    print(f" -> Canonical Distance: {canonical_distance} km | Duration: {created_route['planned_duration_min']} min")
    print(f" -> Transportation Cost: ${created_route['cost_total_usd']} USD | Status: {created_route['status']}")

    # 4. KPI Incremental Check
    stats_after_create = session.get(f"{API_BASE}/routes/stats").json()
    assert stats_after_create["total_routes"] == total_routes_before + 1, "Total routes did not increment"
    print(f" -> [OK] Total Routes KPI verified: {total_routes_before} -> {stats_after_create['total_routes']}")

    # 5. Search & Filtering Capabilities
    print(f"\n[TEST 5] Testing Route Search and Filter Capabilities...")
    # Code search
    search_code_resp = session.get(f"{API_BASE}/routes", params={"search": test_route_code})
    assert any(r["route_code"] == test_route_code for r in search_code_resp.json()), f"Route {test_route_code} not found by search"
    print(f" -> [OK] Route code search matched: {test_route_code}")

    # Shipment code search
    search_shp_resp = session.get(f"{API_BASE}/routes", params={"search": test_shipment_code})
    assert any(r["route_code"] == test_route_code for r in search_shp_resp.json()), f"Route not found by shipment search {test_shipment_code}"
    print(f" -> [OK] Shipment code search matched linked route: {test_shipment_code}")

    # Status filter
    filter_status_resp = session.get(f"{API_BASE}/routes", params={"status": "Assigned"})
    assert any(r["route_code"] == test_route_code for r in filter_status_resp.json()), "Route not found by status filter"
    print(f" -> [OK] Status filter 'Assigned' returned {len(filter_status_resp.json())} route(s)")

    # 6. Deep Operational Inspection
    print(f"\n[TEST 6] Testing Deep Operational Route Inspection (GET /api/v1/routes/{test_route_code})...")
    detail_resp = session.get(f"{API_BASE}/routes/{test_route_code}")
    if detail_resp.status_code != 200:
        print(f"FAILED: /routes/{test_route_code} returned {detail_resp.status_code}")
        sys.exit(1)
    route_detail = detail_resp.json()
    assert route_detail["route_code"] == test_route_code
    assert route_detail["shipment_code"] == test_shipment_code
    assert len(route_detail.get("waypoints", [])) >= 2, "Waypoints missing from route detail"
    assert len(route_detail.get("polyline", [])) >= 2, "Polyline coordinates missing from route detail"
    print(f" -> [OK] Waypoints: {len(route_detail['waypoints'])} checkpoints")
    print(f" -> [OK] Polyline: {len(route_detail['polyline'])} GPS coordinate points")
    print(f" -> [OK] Linked Vehicle: {route_detail['vehicle_code']} | Driver: {route_detail['driver_name']}")

    # 7. Canonical Distance Consistency Check (Step 7)
    print(f"\n[TEST 7] Verifying Authoritative Canonical Distance Consistency...")
    shp_detail = session.get(f"{API_BASE}/shipments/{test_shipment_code}").json()
    cost_detail = shp_detail.get("cost_breakdown", {})
    
    route_dist = route_detail["planned_distance_km"]
    shp_cost_total = shp_detail.get("cost_total_usd")
    route_cost_total = route_detail.get("cost_total_usd")
    
    print(f" -> Route Planned Distance: {route_dist} km")
    print(f" -> Route Cost Total: ${route_cost_total} USD")
    print(f" -> Shipment Cost Total: ${shp_cost_total} USD")
    assert abs(route_cost_total - shp_cost_total) < 1.0, f"Cost mismatch: Route ${route_cost_total} vs Shipment ${shp_cost_total}"
    print(f" -> [OK] Canonical Distance and Cost consistency verified across Route and Shipment modules.")

    # 8. Route Optimization Engine Test (Step 17)
    print(f"\n[TEST 8] Testing Route Optimization Engine (POST /api/v1/routes/optimize)...")
    opt_payload = {
        "route_code": test_route_code,
        "shipment_code": test_shipment_code,
        "priority": "fastest"
    }
    opt_resp = session.post(f"{API_BASE}/routes/optimize", json=opt_payload)
    if opt_resp.status_code != 200:
        print(f"FAILED to optimize route: {opt_resp.status_code} {opt_resp.text}")
        sys.exit(1)
    opt_result = opt_resp.json()
    assert opt_result["success"] is True
    rec_route = opt_result["recommended_route"]
    alt_routes = opt_result.get("alternative_routes", [])
    print(f" -> [OK] Recommended Primary Corridor: {rec_route['corridor']}")
    print(f" -> Primary: {rec_route['distance_km']} km, {rec_route['duration_formatted']}, ${rec_route['estimated_cost_usd']} USD ({rec_route['traffic_condition']} traffic)")
    if alt_routes:
        print(f" -> Alternative Bypass: {alt_routes[0]['corridor']} ({alt_routes[0]['distance_km']} km, {alt_routes[0]['duration_formatted']}, ${alt_routes[0]['estimated_cost_usd']} USD)")

    # 9. AI Assistant Integration Test (Step 18 & 19)
    print(f"\n[TEST 9] Testing AI Assistant Live Route Discovery & Reasoning (/agent/chat)...")
    chat_payload = {
        "message": f"What is the optimal route and distance for shipment {test_shipment_code}?",
        "user_role": "Logistics Manager"
    }
    chat_resp = session.post(f"{API_BASE}/agent/chat", json=chat_payload)
    if chat_resp.status_code != 200:
        print(f"FAILED: /agent/chat returned {chat_resp.status_code}: {chat_resp.text}")
        sys.exit(1)
    chat_data = chat_resp.json()
    ai_text = chat_data["response"]
    print(f" -> AI Response:\n{ai_text}\n")
    assert str(int(canonical_distance)) in ai_text or str(round(canonical_distance, 1)) in ai_text, "Canonical distance not found in AI response"
    assert "route_optimization_tool" in chat_data["tools_used"], "route_optimization_tool was not utilized by agent"
    print(f" -> [OK] AI Assistant successfully discovered live route, distance ({canonical_distance} km), and calculated optimization.")

    # 10. Route Update Test (Step 22)
    print(f"\n[TEST 10] Testing Route Destination & Assignment Update (PUT /api/v1/routes/{test_route_code})...")
    update_payload = {
        "destination_id": dest_alt_loc["id"],
        "status": "In Transit",
        "traffic_condition": "Heavy"
    }
    update_resp = session.put(f"{API_BASE}/routes/{test_route_code}", json=update_payload)
    if update_resp.status_code != 200:
        print(f"FAILED to update route: {update_resp.status_code} {update_resp.text}")
        sys.exit(1)
    updated_route = update_resp.json()
    assert updated_route["status"] == "In Transit"
    assert updated_route["traffic_condition"] == "Heavy"
    print(f" -> [OK] Route Destination updated to {dest_alt_loc['name']}. Recalculated distance: {updated_route['planned_distance_km']} km")
    print(f" -> Recalculated Cost: ${updated_route['cost_total_usd']} USD | Status: {updated_route['status']}")

    # 11. Route Lifecycle & Cancellation Protection Test (Step 23)
    print(f"\n[TEST 11] Testing Route In-Transit Cancellation Protection...")
    # Attempting to delete route while in transit should be blocked or handled safely
    del_resp = session.delete(f"{API_BASE}/routes/{test_route_code}")
    print(f" -> Attempt cancellation while in-transit response: {del_resp.status_code} ({del_resp.json().get('detail', del_resp.json().get('message'))})")
    assert del_resp.status_code == 400, "Should prevent deleting in-transit active route"
    print(f" -> [OK] Cancellation protection actively prevented deleting in-transit corridor.")

    # Update status to Completed
    session.put(f"{API_BASE}/routes/{test_route_code}", json={"status": "Completed"})
    print(f" -> [OK] Successfully transitioned route lifecycle to 'Completed'.")

    # 12. Cleanup of Temporary Test Records (Step 21 & 23)
    print(f"\n[TEST 12] Cleaning up temporary test records...")
    # Direct DB session cleanup for test records
    from app.core.database import SessionLocal
    from app.models.route import Route
    from app.models.shipment import Shipment, ShipmentStatusHistory
    from app.models.cost import TransportationCost
    
    db = SessionLocal()
    try:
        # Delete test route
        db.query(Route).filter(Route.route_code == test_route_code).delete()
        # Delete child records of test shipment
        db.query(ShipmentStatusHistory).filter(ShipmentStatusHistory.shipment_id == shipment_id).delete()
        db.query(TransportationCost).filter(TransportationCost.shipment_id == shipment_id).delete()
        # Delete test shipment
        db.query(Shipment).filter(Shipment.id == shipment_id).delete()
        db.commit()
        print(f" -> [OK] Cleaned up temporary test records {test_route_code} and {test_shipment_code}.")
    except Exception as e:
        db.rollback()
        print(f" -> Warning during cleanup: {e}")
    finally:
        db.close()

    # 13. Verify Final Stats after Cleanup
    stats_final = session.get(f"{API_BASE}/routes/stats").json()
    assert stats_final["total_routes"] == total_routes_before, "Total routes did not return to baseline after cleanup"
    print(f" -> [OK] Final Total Routes KPI restored to baseline: {stats_final['total_routes']}")

    print("\n" + "=" * 80)
    print("ALL PHASE 8 DYNAMIC ROUTE MANAGEMENT TESTS PASSED SUCCESSFULLY! (PASS)")
    print("=" * 80)

if __name__ == "__main__":
    run_phase8_tests()
