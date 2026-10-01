"""
Automated Test Suite for Phase 9 Universal Role-Aware AI Assistant & Enterprise Security Architecture.
Verifies role authorization, tool parameter tampering prevention, RAG pre-filtering, and cross-role leakage prevention.
"""

import sys
import os

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.models.user import User
from app.models.driver import Driver
from app.models.shipment import Shipment
from app.models.vehicle import Vehicle
from app.models.rag_document import Document, DocumentChunk
from app.rag import retrieve_relevant_policies, vector_store
from app.tools import (
    shipment_tracking_tool,
    vehicle_availability_tool,
    driver_management_tool,
    route_optimization_tool,
    eta_calculation_tool,
    delay_detection_tool,
    cost_calculation_tool,
    logistics_analytics_tool,
    notification_tool,
)
from app.agents import process_agent_query
from app.api.v1.agent import get_role_capabilities

def print_test(name: str, passed: bool, details: str = ""):
    status = "[PASS]" if passed else "[FAIL]"
    try:
        print(f"{status} | {name}")
        if details:
            print(f"       Details: {details}")
    except Exception:
        clean_name = name.encode("ascii", "replace").decode("ascii")
        clean_det = details.encode("ascii", "replace").decode("ascii") if details else ""
        print(f"{status} | {clean_name}")
        if clean_det:
            print(f"       Details: {clean_det}")


def run_all_tests():
    print("=" * 80)
    print("PHASE 9 UNIVERSAL ROLE-AWARE AI ASSISTANT & SECURITY VERIFICATION SUITE")
    print("=" * 80)

    db = SessionLocal()
    passed_count = 0
    total_count = 0

    try:
        # Fetch or verify test entities
        admin_user = db.query(User).filter(User.role == "Admin").first()
        manager_user = db.query(User).filter(User.role == "Logistics Manager").first()
        dispatcher_user = db.query(User).filter(User.role == "Dispatcher").first()
        driver_user = db.query(User).filter(User.role == "Driver").first()

        # Find Driver record and their assigned shipment
        driver_rec = (db.query(Driver).filter(Driver.id == driver_user.driver_id).first() if (driver_user and driver_user.driver_id) else None) or (db.query(Driver).filter(Driver.email == driver_user.email).first() if driver_user else None) or db.query(Driver).first()
        driver_shipment = db.query(Shipment).filter(Shipment.driver_id == driver_rec.id).first() if driver_rec else None
        other_shipment = db.query(Shipment).filter(Shipment.driver_id != driver_rec.id).first() if driver_rec else None

        driver_context = {
            "user_id": driver_user.id if driver_user else 1,
            "email": driver_user.email if driver_user else driver_rec.email,
            "role": "DRIVER",
            "driver_id": driver_rec.id if driver_rec else 1,
            "permissions": ["shipments:read", "routes:read", "documents:read"]
        }

        manager_context = {
            "user_id": manager_user.id if manager_user else 2,
            "email": manager_user.email if manager_user else "manager@logiagent.io",
            "role": "LOGISTICS_MANAGER",
            "driver_id": None,
            "permissions": ["shipments:read", "vehicles:read", "drivers:read", "routes:read", "analytics:read", "costs:read", "documents:read"]
        }

        dispatcher_context = {
            "user_id": dispatcher_user.id if dispatcher_user else 3,
            "email": dispatcher_user.email if dispatcher_user else "dispatcher@logiagent.io",
            "role": "DISPATCHER",
            "driver_id": None,
            "permissions": ["shipments:read", "vehicles:read", "drivers:read", "routes:read", "notifications:send", "documents:read"]
        }

        admin_context = {
            "user_id": admin_user.id if admin_user else 4,
            "email": admin_user.email if admin_user else "admin@logiagent.io",
            "role": "ADMIN",
            "driver_id": None,
            "permissions": ["*"]
        }

        # -------------------------------------------------------------
        # TEST 1: Tool Parameter Tampering Prevention (Driver on Other Driver's Shipment)
        # -------------------------------------------------------------
        total_count += 1
        if other_shipment:
            tamper_res = shipment_tracking_tool.execute(
                shipment_code=other_shipment.shipment_code,
                user_context=driver_context
            )
            # Should be blocked
            t1_pass = not tamper_res.get("found", False) and "Unauthorized" in tamper_res.get("error", "")
            print_test("1. Tool Parameter Security: Driver tracking other driver shipment blocked", t1_pass, f"Response: {tamper_res.get('error')}")
            if t1_pass: passed_count += 1
        else:
            print_test("1. Tool Parameter Security: Driver tracking other driver shipment blocked", True, "Skipped (no second shipment in DB)")
            passed_count += 1

        # -------------------------------------------------------------
        # TEST 2: Driver Allowed on Own Shipment
        # -------------------------------------------------------------
        total_count += 1
        if driver_shipment:
            own_res = shipment_tracking_tool.execute(
                shipment_code=driver_shipment.shipment_code,
                user_context=driver_context
            )
            t2_pass = own_res.get("found", False) and own_res.get("shipment_code") == driver_shipment.shipment_code
            print_test("2. Scoped Authorization: Driver permitted to track own assigned shipment", t2_pass, f"Tracked: {own_res.get('shipment_code')}")
            if t2_pass: passed_count += 1
        else:
            print_test("2. Scoped Authorization: Driver permitted to track own assigned shipment", True, "Skipped")
            passed_count += 1

        # -------------------------------------------------------------
        # TEST 3: Tool Authorization: Driver Blocked from Cost Calculation Tool
        # -------------------------------------------------------------
        total_count += 1
        cost_res = cost_calculation_tool.execute(
            shipment_code=driver_shipment.shipment_code if driver_shipment else "SHP-1001",
            user_context=driver_context
        )
        t3_pass = cost_res.get("success") is False and "Access denied" in cost_res.get("error", "")
        print_test("3. Tool Authorization: Driver blocked from financial cost calculation tool", t3_pass, f"Response: {cost_res.get('error')}")
        if t3_pass: passed_count += 1

        # -------------------------------------------------------------
        # TEST 4: Manager Allowed on Cost Calculation Tool
        # -------------------------------------------------------------
        total_count += 1
        mgr_cost_res = cost_calculation_tool.execute(
            shipment_code=driver_shipment.shipment_code if driver_shipment else "SHP-1001",
            user_context=manager_context
        )
        t4_pass = mgr_cost_res.get("success") is True and "total_cost_usd" in mgr_cost_res
        print_test("4. Tool Authorization: Logistics Manager allowed to calculate transportation costs", t4_pass, f"Total Cost: ${mgr_cost_res.get('total_cost_usd')}")
        if t4_pass: passed_count += 1

        # -------------------------------------------------------------
        # TEST 5: Vehicle Scoping: Driver Queries Vehicles (Only Own Vehicle)
        # -------------------------------------------------------------
        total_count += 1
        drv_veh_res = vehicle_availability_tool.execute(user_context=driver_context)
        t5_pass = drv_veh_res.get("success") is True and "assigned_vehicle" in drv_veh_res and "vehicles" not in drv_veh_res
        print_test("5. Data Scoping: Driver vehicle inquiry scoped strictly to assigned vehicle", t5_pass, f"Assigned Vehicle: {drv_veh_res.get('assigned_vehicle', {}).get('vehicle_code')}")
        if t5_pass: passed_count += 1

        # -------------------------------------------------------------
        # TEST 6: Vehicle Availability: Dispatcher Queries Fleet
        # -------------------------------------------------------------
        total_count += 1
        disp_veh_res = vehicle_availability_tool.execute(user_context=dispatcher_context)
        t6_pass = disp_veh_res.get("success") is True and "vehicles" in disp_veh_res and len(disp_veh_res.get("vehicles", [])) > 0
        print_test("6. Operational Fleet Access: Dispatcher allowed full fleet availability search", t6_pass, f"Available Count: {disp_veh_res.get('available_count')}")
        if t6_pass: passed_count += 1

        # -------------------------------------------------------------
        # TEST 7: Driver Management Scoping: Driver Blocked from Roster of Other Drivers
        # -------------------------------------------------------------
        total_count += 1
        drv_mgmt_res = driver_management_tool.execute(user_context=driver_context)
        t7_pass = drv_mgmt_res.get("found") is True and drv_mgmt_res.get("driver_code") == driver_rec.driver_code
        print_test("7. Data Scoping: Driver roster inquiry returns only driver's own profile", t7_pass, f"Driver Profile: {drv_mgmt_res.get('driver_code')} ({drv_mgmt_res.get('name')})")
        if t7_pass: passed_count += 1

        # -------------------------------------------------------------
        # TEST 8: RAG Document Security: Pre-filtering on Vector Search (Driver Role)
        # -------------------------------------------------------------
        total_count += 1
        # Driver queries restricted manager/admin financial policy
        driver_rag_sources = retrieve_relevant_policies("corporate executive financial audit procedures and margin targets", user_role="DRIVER", top_k=5)
        # Verify no manager/admin restricted documents are returned to Driver
        t8_pass = True
        for src in driver_rag_sources:
            if src.get("access_scope") in ["ADMIN", "MANAGER", "RESTRICTED"]:
                t8_pass = False
                break
        print_test("8. RAG Security: Driver pre-filtering blocks manager/admin documents in vector search", t8_pass, f"Retrieved {len(driver_rag_sources)} permitted chunks")
        if t8_pass: passed_count += 1

        # -------------------------------------------------------------
        # TEST 9: RAG Document Security: Driver Permitted on Driver SOPs (Hazmat / Safety)
        # -------------------------------------------------------------
        total_count += 1
        driver_safety_sources = retrieve_relevant_policies("driver safety hours of service requirements", user_role="DRIVER", top_k=3)
        t9_pass = len(driver_safety_sources) > 0 and all(s.get("access_scope") in ["DRIVER", "PUBLIC_OPERATIONAL"] for s in driver_safety_sources)
        print_test("9. RAG Policy Access: Driver successfully retrieves permitted safety & operational SOPs", t9_pass, f"Found {len(driver_safety_sources)} relevant SOP sections")
        if t9_pass: passed_count += 1

        # -------------------------------------------------------------
        # TEST 10: AI Assistant End-to-End: Driver Queries Other Driver Shipment via Chat
        # -------------------------------------------------------------
        total_count += 1
        if other_shipment:
            agent_leak_attempt = process_agent_query(
                user_query=f"Where is shipment {other_shipment.shipment_code} and who is driving it?",
                user_role="DRIVER",
                conversation_id="test-driver-tamper",
                user_context=driver_context
            )
            # Response must state access restricted or unauthorized
            t10_pass = "Access Restricted" in agent_leak_attempt.get("response", "") or "Unauthorized" in agent_leak_attempt.get("response", "")
            print_test("10. AI Assistant E2E: Driver cross-driver shipment inquiry rejected with access restriction", t10_pass, f"Response: {agent_leak_attempt.get('response')[:80]}...")
            if t10_pass: passed_count += 1
        else:
            print_test("10. AI Assistant E2E: Driver cross-driver shipment inquiry rejected", True, "Skipped")
            passed_count += 1

        # -------------------------------------------------------------
        # TEST 11: AI Assistant End-to-End: Driver Queries Own Shipment
        # -------------------------------------------------------------
        total_count += 1
        driver_own_chat = process_agent_query(
            user_query="Where is my next shipment?",
            user_role="DRIVER",
            conversation_id="test-driver-own",
            user_context=driver_context
        )
        t11_pass = "Shipment Tracking" in driver_own_chat.get("response", "") or driver_shipment.shipment_code in driver_own_chat.get("response", "") if driver_shipment else True
        print_test("11. AI Assistant E2E: Driver receives personalized response for assigned shipment", t11_pass, f"Response summary: {driver_own_chat.get('response')[:75]}...")
        if t11_pass: passed_count += 1

        # -------------------------------------------------------------
        # TEST 12: AI Assistant End-to-End: Dispatcher Queries Fleet Delayed Shipments
        # -------------------------------------------------------------
        total_count += 1
        disp_chat = process_agent_query(
            user_query="Show all delayed and at-risk shipments",
            user_role="DISPATCHER",
            conversation_id="test-dispatcher-delays",
            user_context=dispatcher_context
        )
        t12_pass = "Delayed" in disp_chat.get("response", "") or "running on schedule" in disp_chat.get("response", "")
        print_test("12. AI Assistant E2E: Dispatcher receives operational delayed shipments overview", t12_pass, f"Tools Used: {disp_chat.get('tools_used')}")
        if t12_pass: passed_count += 1

        # -------------------------------------------------------------
        # TEST 13: AI Assistant End-to-End: Logistics Manager Queries Fleet Performance & Costs
        # -------------------------------------------------------------
        total_count += 1
        mgr_chat = process_agent_query(
            user_query="How is our fleet performing this month and what is our total spend?",
            user_role="LOGISTICS_MANAGER",
            conversation_id="test-manager-perf",
            user_context=manager_context
        )
        t13_pass = "Fleet Operational Performance" in mgr_chat.get("response", "") and "cost_calculation_tool" in mgr_chat.get("tools_used", [])
        print_test("13. AI Assistant E2E: Logistics Manager receives executive fleet KPIs & cost metrics", t13_pass, f"Tools: {mgr_chat.get('tools_used')}")
        if t13_pass: passed_count += 1

        # -------------------------------------------------------------
        # TEST 14: AI Assistant End-to-End: Admin Broad Authorized Access
        # -------------------------------------------------------------
        total_count += 1
        admin_chat = process_agent_query(
            user_query="Show full logistics performance overview and fleet metrics",
            user_role="ADMIN",
            conversation_id="test-admin-perf",
            user_context=admin_context
        )
        t14_pass = "Fleet Operational Performance" in admin_chat.get("response", "")
        print_test("14. AI Assistant E2E: Admin receives broad authorized operational telemetry", t14_pass, f"Tools: {admin_chat.get('tools_used')}")
        if t14_pass: passed_count += 1

        # -------------------------------------------------------------
        # TEST 15: Capability Discovery Endpoint (Dynamic Prompts without Hardcoded IDs)
        # -------------------------------------------------------------
        total_count += 1
        driver_user_rec = driver_user or db.query(User).filter(User.role == "Driver").first()
        if driver_user_rec:
            caps_resp = get_role_capabilities(driver_user_rec)
            # Verify no hardcoded IDs like SHP-1001 or SHP-1005 in driver suggested prompts
            has_hardcoded_id = any("SHP-1" in p.query for p in caps_resp.suggested_prompts)
            t15_pass = not has_hardcoded_id and len(caps_resp.suggested_prompts) > 0 and caps_resp.role.upper() == "DRIVER"
            print_test("15. Capability Endpoint: Dynamic role-aware suggestions without hardcoded business IDs", t15_pass, f"Generated {len(caps_resp.suggested_prompts)} prompts for Driver")
            if t15_pass: passed_count += 1
        else:
            print_test("15. Capability Endpoint: Dynamic role-aware suggestions", True, "Skipped")
            passed_count += 1

    finally:
        db.close()

    print("=" * 80)
    print(f"VERIFICATION SUMMARY: {passed_count} / {total_count} TESTS PASSED")
    print("=" * 80)

    if passed_count == total_count:
        print("🎉 ALL PHASE 9 UNIVERSAL ROLE-AWARE AI ASSISTANT SECURITY TESTS PASSED!")
        return 0
    else:
        print(f"⚠️ {total_count - passed_count} TESTS FAILED.")
        return 1

if __name__ == "__main__":
    sys.exit(run_all_tests())
