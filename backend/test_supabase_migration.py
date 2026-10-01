import sys
import os
from datetime import datetime

# Configure utf-8 standard output for Windows console
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

from app.core.config import settings
from app.core.database import engine, SessionLocal, Base
from app.data.seed_data import seed_database
from app.models.user import User
from app.models.customer import Customer
from app.models.location import DeliveryLocation
from app.models.driver import Driver
from app.models.vehicle import Vehicle
from app.models.order import Order
from app.models.shipment import Shipment, ShipmentStatusHistory
from app.models.route import Route
from app.models.cost import TransportationCost
from app.models.notification import Notification
from app.models.rag_document import DocumentChunk

from app.tools import TOOLS_REGISTRY
from app.agents.logi_agent import process_agent_query

def run_supabase_tests():
    print("=" * 70)
    print("LOGIAGENT SUPABASE POSTGRESQL MIGRATION & VERIFICATION")
    masked_url = settings.DATABASE_URL.split('@')[-1] if '@' in settings.DATABASE_URL else settings.DATABASE_URL[:25]
    print(f"DATABASE_URL Host: {masked_url}")
    print("=" * 70)

    # 1. Test Connection
    print("\n[STEP 1] Testing Database Connection to Supabase...")
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version();"))
            db_version = result.scalar()
            print(f" -> Database Connection: SUCCESS")
            print(f"    Supabase Engine: {db_version.split(',')[0] if db_version else 'PostgreSQL'}")
    except Exception as e:
        print(f" -> Database Connection: FAILED: {e}")
        return False

    # 2. Database Schema Creation
    print("\n[STEP 2] Creating / Verifying Schema Tables...")
    try:
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f" -> Tables created ({len(tables)} tables): {sorted(tables)}")
        
        expected_tables = [
            "users", "customers", "delivery_locations", "drivers",
            "vehicles", "orders", "shipments", "shipment_status_history",
            "routes", "transportation_costs", "notifications", "document_chunks"
        ]
        for t in expected_tables:
            assert t in tables, f"Missing table: {t}"
        print(" -> Schema Verification: PASS")
    except Exception as e:
        print(f" -> Schema Creation: FAILED: {e}")
        return False

    # 3. Seed Realistic Logistics Data
    print("\n[STEP 3] Seeding Relational Logistics Dataset into Supabase...")
    try:
        seed_database(force_recreate=False)
        print(" -> Seeding: SUCCESS")
    except Exception as e:
        print(f" -> Seeding: FAILED: {e}")
        return False

    # 4. Count and Verify Relational Integrity
    print("\n[STEP 4] Verifying Table Record Counts & Relationships...")
    db: Session = SessionLocal()
    counts = {}
    try:
        counts["users"] = db.query(User).count()
        counts["customers"] = db.query(Customer).count()
        counts["delivery_locations"] = db.query(DeliveryLocation).count()
        counts["drivers"] = db.query(Driver).count()
        counts["vehicles"] = db.query(Vehicle).count()
        counts["orders"] = db.query(Order).count()
        counts["shipments"] = db.query(Shipment).count()
        counts["shipment_status_history"] = db.query(ShipmentStatusHistory).count()
        counts["routes"] = db.query(Route).count()
        counts["transportation_costs"] = db.query(TransportationCost).count()
        counts["notifications"] = db.query(Notification).count()
        counts["document_chunks"] = db.query(DocumentChunk).count()

        for table_name, count in counts.items():
            print(f"    - {table_name:25s}: {count:3d} records")

        # Verify relational integrity
        shp1 = db.query(Shipment).filter(Shipment.shipment_code == "SHP-1001").first()
        assert shp1 is not None
        assert shp1.driver_id is not None
        assert shp1.vehicle_id is not None
        assert shp1.origin_id is not None
        assert shp1.destination_id is not None
        
        driver = db.query(Driver).filter(Driver.id == shp1.driver_id).first()
        vehicle = db.query(Vehicle).filter(Vehicle.id == shp1.vehicle_id).first()
        cost = db.query(TransportationCost).filter(TransportationCost.shipment_id == shp1.id).first()
        route = db.query(Route).filter(Route.shipment_id == shp1.id).first()

        print(f" -> Relational Integrity Verified: SHP-1001 -> Driver: {driver.name}, Vehicle: {vehicle.vehicle_code}, Cost: ${cost.total_cost}, Route: {route.route_code}")
        print(" -> Relational/Foreign Keys: PASS")
    except Exception as e:
        print(f" -> Relational Verification: FAILED: {e}")
        return False
    finally:
        db.close()

    # 5. Test Persistence Across Session Restart
    print("\n[STEP 5] Testing Persistence Across Fresh Session...")
    try:
        fresh_db: Session = SessionLocal()
        persisted_shipment = fresh_db.query(Shipment).filter(Shipment.shipment_code == "SHP-1001").first()
        assert persisted_shipment is not None and persisted_shipment.weight_kg == 14500.0
        persisted_count = fresh_db.query(Shipment).count()
        assert persisted_count >= 36
        fresh_db.close()
        print(f" -> Persistence Verification: PASS ({persisted_count} shipments persisted)")
    except Exception as e:
        print(f" -> Persistence Verification: FAILED: {e}")
        return False

    # 6. Test All 9 Agent Tools Direct Supabase DB Execution
    print("\n[STEP 6] Testing All 9 Agent Tools with Supabase DB...")
    tool_results = {}
    
    # 1. Shipment Tracking Tool
    res1 = TOOLS_REGISTRY["shipment_tracking_tool"].execute(shipment_code="SHP-1001")
    tool_results["Shipment Tracking Tool"] = res1.get("found") is True and res1.get("shipment_code") == "SHP-1001"

    # 2. Vehicle Availability Tool
    res2 = TOOLS_REGISTRY["vehicle_availability_tool"].execute(min_capacity_kg=1500.0)
    tool_results["Vehicle Availability Tool"] = res2.get("available_vehicles_count", 0) > 0 and len(res2.get("vehicles", [])) > 0

    # 3. Driver Management Tool
    res3 = TOOLS_REGISTRY["driver_management_tool"].execute(status="Available")
    tool_results["Driver Management Tool"] = res3.get("count", 0) > 0 and len(res3.get("drivers", [])) > 0

    # 4. Route Optimization Tool
    res4 = TOOLS_REGISTRY["route_optimization_tool"].execute(origin_id=1, destination_id=2)
    tool_results["Route Optimization Tool"] = res4.get("success") is True and res4.get("recommended_route", {}).get("distance_km", 0) > 0

    # 5. ETA Calculation Tool
    res5 = TOOLS_REGISTRY["eta_calculation_tool"].execute(shipment_code="SHP-1001")
    tool_results["ETA Calculation Tool"] = res5.get("success") is True and "calculated_eta" in res5

    # 6. Delay Detection Tool
    res6 = TOOLS_REGISTRY["delay_detection_tool"].execute(min_delay_minutes=0)
    tool_results["Delay Detection Tool"] = res6.get("delayed_count", 0) > 0

    # 7. Cost Calculation Tool
    res7 = TOOLS_REGISTRY["cost_calculation_tool"].execute(shipment_code="SHP-1001")
    tool_results["Cost Calculation Tool"] = res7.get("success") is True and res7.get("total_cost_usd", 0) > 0

    # 8. Logistics Analytics Tool
    res8 = TOOLS_REGISTRY["logistics_analytics_tool"].execute()
    tool_results["Logistics Analytics Tool"] = res8.get("success") is True and res8.get("performance_summary", {}).get("total_shipments", 0) >= 36

    # 9. Notification Tool
    res9 = TOOLS_REGISTRY["notification_tool"].execute(
        title="Supabase Test Notification",
        message="Testing real notification insert to Supabase PostgreSQL",
        notification_type="critical_event",
        severity="low",
        recipient="ops@logiagent.io"
    )
    tool_results["Notification Tool"] = res9.get("success") is True and res9.get("notification_id") is not None

    for tool_name, passed in tool_results.items():
        print(f"    - {tool_name:30s}: {'PASS' if passed else 'FAIL'}")

    all_tools_passed = all(tool_results.values())
    print(f" -> 9 Tools Verification: {'PASS' if all_tools_passed else 'FAIL'}")

    # 7. Test 6 Required Agent Queries End-to-End
    print("\n[STEP 7] Testing 6 Required Agent Queries End-to-End...")
    test_queries = [
        ("Where is shipment SHP-1001?", "SHP-1001"),
        ("Show me all delayed shipments.", "delayed"),
        ("Which vehicle is available for a 1500 kg shipment?", "Available"),
        ("Who is the driver assigned to SHP-1001?", "Robert McCall"),
        ("Show the transportation cost for SHP-1001.", "$"),
        ("How many shipments are currently in transit?", "in-transit"),
    ]

    query_results = []
    for query, expected_keyword in test_queries:
        result = process_agent_query(query)
        has_tool = len(result.get("tools_used", [])) > 0
        content = result.get("response", "")
        keyword_match = expected_keyword.lower() in content.lower()
        passed = has_tool and keyword_match
        query_results.append(passed)
        print(f"    - Query: \"{query}\"")
        print(f"      Tools Used: {result.get('tools_used')} | Match '{expected_keyword}': {keyword_match} | Success: {'PASS' if passed else 'FAIL'}")
        safe_excerpt = content[:100].replace('\n', ' ')
        print(f"      Response Excerpt: {safe_excerpt}...")

    all_queries_passed = all(query_results)
    print(f"\n -> 6 Agent Queries: {'PASS' if all_queries_passed else 'FAIL'}")

    print("\n" + "=" * 70)
    overall = all_tools_passed and all_queries_passed
    print(f"OVERALL SUPABASE DATABASE VERIFICATION: {'PASS' if overall else 'FAIL'}")
    print("=" * 70)
    return counts, tool_results, overall

if __name__ == "__main__":
    run_supabase_tests()
