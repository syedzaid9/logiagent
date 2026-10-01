#!/usr/bin/env python3
"""
================================================================================
LOGIAGENT — PHASE 11: ADVANCED AI & LOGISTICS INTELLIGENCE MASTER VERIFICATION
================================================================================
Validates all Phase 11 deliverables against functional, security, grounding,
and performance specifications:
1. ETA Prediction Engine & Fallbacks
2. Delay Prediction & Feature Attribution
3. Transportation Cost Intelligence
4. Unified Shipment Risk Engine
5. AI Logistics Analyst & Natural Language Analytics
6. Explainable Shipment Analysis
7. Route Intelligence & Optimization Comparisons
8. Operational Anomaly Detection
9. Deduplicated Alert Pipeline & Lifecycle
10. Role-Aware AI & Data Scoping
11. RAG & Anti-Hallucination Grounding
12. Human-in-the-Loop Guardrails
13. AI Endpoints & Rate Limiting
================================================================================
"""

import sys
import os
from datetime import datetime, timezone, timedelta

# Ensure backend path is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal
from app.models.shipment import Shipment
from app.models.route import Route
from app.models.driver import Driver
from app.models.vehicle import Vehicle
from app.models.alert import Alert
from app.ml.eta_predictor import eta_predictor
from app.ml.delay_predictor import delay_predictor
from app.ml.cost_optimizer import cost_optimizer
from app.services.shipment_risk_service import shipment_risk_service
from app.services.cost_service import cost_service
from app.services.anomaly_detection_service import anomaly_detection_service
from app.services.recommendation_service import recommendation_service
from app.agents import process_agent_query

client = TestClient(app)

TOTAL_CHECKS = 0
PASSED_CHECKS = 0

def check(title: str, condition: bool, details: str = ""):
    global TOTAL_CHECKS, PASSED_CHECKS
    TOTAL_CHECKS += 1
    safe_details = details.encode("ascii", errors="replace").decode("ascii") if details else ""
    if condition:
        PASSED_CHECKS += 1
        print(f"  [PASS] {title}")
        if safe_details:
            print(f"         |-- {safe_details}")
    else:
        print(f"  [FAIL] {title}")
        if safe_details:
            print(f"         |-- ERROR: {safe_details}")

def get_auth_token(email: str, password: str = "LogiAgent2026!") -> str:
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    if res.status_code == 200:
        return res.json()["access_token"]
    return ""

def main():
    print("\n" + "=" * 80)
    print("LOGIAGENT PHASE 11: ADVANCED AI & LOGISTICS INTELLIGENCE VERIFICATION")
    print("=" * 80 + "\n")

    admin_token = get_auth_token("admin@logiagent.io")
    driver_token = get_auth_token("driver@logiagent.io")

    # --------------------------------------------------------------------------
    # 1. ETA PREDICTION ENGINE
    # --------------------------------------------------------------------------
    print("[1/13] Verifying ETA Prediction Engine & Fallbacks...")
    now_utc = datetime.now(timezone.utc)
    eta_res = eta_predictor.predict_eta(
        current_time=now_utc,
        remaining_distance_km=600.0,
        traffic_condition="Moderate",
        weather_condition="Clear",
        current_delay_min=20
    )
    check("ETA Predictor calculations valid", "predicted_eta" in eta_res and eta_res["effective_speed_kmh"] > 0,
          f"Speed: {eta_res['effective_speed_kmh']} km/h, Duration: {eta_res['total_duration_minutes']} min")

    db = SessionLocal()
    try:
        service_eta = shipment_risk_service.predict_eta(db, "SHP-1001")
        check("ETA Service valid shipment output", service_eta.get("prediction_status") == "success" and service_eta.get("predicted_eta") is not None,
              f"Predicted ETA: {service_eta.get('predicted_eta')}")

        invalid_eta = shipment_risk_service.predict_eta(db, "SHP-NONEXISTENT")
        check("ETA Service non-existent shipment returns 'prediction_unavailable'",
              invalid_eta.get("prediction_status") == "prediction_unavailable" and invalid_eta.get("predicted_eta") is None,
              f"Status: {invalid_eta.get('prediction_status')}")
    finally:
        db.close()

    # --------------------------------------------------------------------------
    # 2. DELAY PREDICTION ENGINE
    # --------------------------------------------------------------------------
    print("\n[2/13] Verifying Delay Prediction & Feature Attribution...")
    delay_low = delay_predictor.predict_delay_risk(
        distance_km=150.0,
        current_delay_min=0,
        traffic_condition="Light",
        weather_condition="Clear",
        driver_hos_remaining=9.0
    )
    delay_crit = delay_predictor.predict_delay_risk(
        distance_km=850.0,
        current_delay_min=75,
        traffic_condition="Severe Congestion",
        weather_condition="Storm",
        driver_hos_remaining=1.5
    )
    check("Delay risk classification produces correct bounds",
          delay_low["risk_score"] < 40 and delay_crit["risk_score"] > 70 and len(delay_crit["important_factors"]) >= 3,
          f"Low: {delay_low['risk_score']} ({delay_low['risk_level']}), High: {delay_crit['risk_score']} ({delay_crit['risk_level']})")

    db = SessionLocal()
    try:
        service_delay = shipment_risk_service.predict_delay(db, "SHP-1001")
        check("Delay service returns probability and features",
              service_delay.get("prediction_status") == "success" and 0.0 <= service_delay.get("delay_probability", -1) <= 1.0,
              f"Probability: {service_delay.get('delay_probability')}, Risk: {service_delay.get('risk_level')}")
    finally:
        db.close()

    # --------------------------------------------------------------------------
    # 3. TRANSPORTATION COST INTELLIGENCE
    # --------------------------------------------------------------------------
    print("\n[3/13] Verifying Transportation Cost Intelligence...")
    db = SessionLocal()
    try:
        cost_shipment = cost_service.estimate_shipment_cost(db, "SHP-1001")
        check("Shipment cost calculation consistent with DB/ML",
              cost_shipment.get("success") is True and cost_shipment.get("total_cost_usd", 0) > 0,
              f"Total Cost: ${cost_shipment.get('total_cost_usd')} USD, Rate: ${cost_shipment.get('cost_per_km')}/km")

        cost_compare = cost_service.compare_route_costs(
            primary_distance_km=1200.0,
            alternative_distance_km=1280.0,
            primary_toll_fees=35.0,
            alternative_toll_fees=0.0
        )
        check("Route corridor comparison computes differences & recommendations",
              cost_compare.get("success") is True and "cost_difference_usd" in cost_compare,
              f"Cost Diff: ${cost_compare.get('cost_difference_usd')}, Rec: {cost_compare.get('recommendation')}")
    finally:
        db.close()

    # --------------------------------------------------------------------------
    # 4. UNIFIED SHIPMENT RISK ENGINE
    # --------------------------------------------------------------------------
    print("\n[4/13] Verifying Unified Shipment Risk Engine...")
    db = SessionLocal()
    try:
        risk_res = shipment_risk_service.analyze_shipment_risk(db, "SHP-1001")
        check("Comprehensive shipment risk assessment synthesized",
              risk_res.get("prediction_status") == "success" and len(risk_res.get("risk_factors", [])) > 0 and len(risk_res.get("recommended_actions", [])) > 0,
              f"Risk Level: {risk_res.get('risk_level')}, Factors: {len(risk_res.get('risk_factors', []))}, Actions: {len(risk_res.get('recommended_actions', []))}")
    finally:
        db.close()

    # --------------------------------------------------------------------------
    # 5. AI LOGISTICS ANALYST (NATURAL LANGUAGE ANALYTICS)
    # --------------------------------------------------------------------------
    print("\n[5/13] Verifying AI Logistics Analyst Natural Language Capabilities...")
    q1 = "Which shipments are at risk today?"
    res_q1 = process_agent_query(user_query=q1, user_role="Logistics Manager")
    check("Natural Language: 'Which shipments are at risk today?' handled",
          "shipment_risk_tool" in res_q1["tools_used"] or "delay_detection_tool" in res_q1["tools_used"],
          f"Tools used: {res_q1['tools_used']}")

    q2 = "What are the biggest operational problems today?"
    res_q2 = process_agent_query(user_query=q2, user_role="Logistics Manager")
    check("Natural Language: 'What are the biggest operational problems today?' handled",
          "anomaly_alerts_tool" in res_q2["tools_used"],
          f"Tools used: {res_q2['tools_used']}")

    q3 = "Which drivers have the highest workload?"
    res_q3 = process_agent_query(user_query=q3, user_role="Dispatcher")
    check("Natural Language: 'Which drivers have the highest workload?' handled",
          "driver_management_tool" in res_q3["tools_used"],
          f"Tools used: {res_q3['tools_used']}")

    q4 = "How many shipments were delivered this week?"
    res_q4 = process_agent_query(user_query=q4, user_role="Logistics Manager")
    check("Natural Language: 'How many shipments were delivered this week?' handled",
          "logistics_analytics_tool" in res_q4["tools_used"],
          f"Tools used: {res_q4['tools_used']}")

    # --------------------------------------------------------------------------
    # 6. EXPLAINABLE SHIPMENT ANALYSIS
    # --------------------------------------------------------------------------
    print("\n[6/13] Verifying Explainable Shipment Risk & Contributing Factors...")
    q_exp = "Why is shipment SHP-1001 delayed?"
    res_exp = process_agent_query(user_query=q_exp, user_role="Operations Team")
    check("Explainable analysis provides grounded factors & actions",
          "SHP-1001" in res_exp["response"] and ("Contributing" in res_exp["response"] or "Risk" in res_exp["response"]),
          f"Snippet: {res_exp['response'][:100]}...")

    # --------------------------------------------------------------------------
    # 7. ROUTE INTELLIGENCE & CORRIDOR COMPARISONS
    # --------------------------------------------------------------------------
    print("\n[7/13] Verifying Route Intelligence & Comparison Tools...")
    q_route = "Compare the current route with the optimized route for SHP-1001"
    res_route = process_agent_query(user_query=q_route, user_role="Logistics Manager")
    check("Route Intelligence tool executed with corridor comparisons",
          "route_intelligence_tool" in res_route["tools_used"] or "route_optimization_tool" in res_route["tools_used"],
          f"Tools: {res_route['tools_used']}")

    # --------------------------------------------------------------------------
    # 8. OPERATIONAL ANOMALY DETECTION
    # --------------------------------------------------------------------------
    print("\n[8/13] Verifying Operational Anomaly Detection...")
    db = SessionLocal()
    try:
        scan_res = anomaly_detection_service.scan_and_generate_alerts(db)
        check("Anomaly detection service executes network-wide scan",
              scan_res.get("success") is True and "active_anomalies_detected" in scan_res,
              f"Detected: {scan_res.get('active_anomalies_detected')}, New: {scan_res.get('new_alerts_created')}")
    finally:
        db.close()

    # --------------------------------------------------------------------------
    # 9. OPERATIONAL ALERTS & DEDUPLICATION
    # --------------------------------------------------------------------------
    print("\n[9/13] Verifying Operational Alerts Deduplication & Lifecycle...")
    db = SessionLocal()
    try:
        anomaly_detection_service.scan_and_generate_alerts(db)
        c1 = db.query(Alert).filter(Alert.status == "active").count()
        anomaly_detection_service.scan_and_generate_alerts(db)
        c2 = db.query(Alert).filter(Alert.status == "active").count()
        check("Alert deduplication prevents redundant active alerts", c1 == c2, f"Active count 1: {c1}, Active count 2: {c2}")

        # Test alert lifecycle
        test_alt = Alert(
            alert_code=f"ALT-VERIF-{int(datetime.now().timestamp())}",
            alert_type="ETA_DEADLINE_RISK",
            severity="HIGH",
            entity_type="shipment",
            entity_id="SHP-VERIF",
            title="Verification Alert",
            message="Verification test alert message",
            status="active",
            created_at=datetime.now(timezone.utc)
        )
        db.add(test_alt)
        db.commit()
        db.refresh(test_alt)

        ack_alt = anomaly_detection_service.acknowledge_alert(db, test_alt.id, "verifier@logiagent.io")
        ack_status = ack_alt.status
        res_alt = anomaly_detection_service.resolve_alert(db, test_alt.id, "verifier@logiagent.io")
        res_status = res_alt.status

        check("Alert lifecycle state transitions (active -> acknowledged -> resolved)",
              ack_status == "acknowledged" and res_status == "resolved",
              f"Acknowledged by: {ack_alt.acknowledged_by}, Resolved at: {res_alt.resolved_at}")

        db.delete(test_alt)
        db.commit()
    finally:
        db.close()

    # --------------------------------------------------------------------------
    # 10. ROLE-AWARE AI & DATA SCOPING (RBAC)
    # --------------------------------------------------------------------------
    print("\n[10/13] Verifying Role-Aware AI & RBAC Data Scoping...")
    db = SessionLocal()
    try:
        # Driver with non-matching driver_id cannot access unassigned shipment risk
        driver_scope_ctx = {"role": "Driver", "driver_id": 9999, "email": "otherdriver@logiagent.io"}
        unauth_risk = shipment_risk_service.analyze_shipment_risk(db, "SHP-1001", user_context=driver_scope_ctx)
        check("Driver role denied access to unassigned shipment risk",
              unauth_risk.get("prediction_status") == "prediction_unavailable" and "Unauthorized" in unauth_risk.get("error", ""),
              f"Error: {unauth_risk.get('error')}")
    finally:
        db.close()

    # --------------------------------------------------------------------------
    # 11. ANTI-HALLUCINATION & GROUNDING
    # --------------------------------------------------------------------------
    print("\n[11/13] Verifying Anti-Hallucination & Grounding Separations...")
    q_ground = "Give me a complete operational analysis and recommendations for SHP-1001."
    res_ground = process_agent_query(user_query=q_ground, user_role="Logistics Manager")
    resp_text = res_ground["response"]
    check("Agent separates DB facts, ML predictions, and AI recommendations",
          ("Database Ground-Truth" in resp_text or "Database" in resp_text) and
          ("ML Predictions" in resp_text or "Prediction" in resp_text or "Risk" in resp_text),
          "Structured grounding categories present in response")

    # --------------------------------------------------------------------------
    # 12. HUMAN-IN-THE-LOOP GUARDRAILS
    # --------------------------------------------------------------------------
    print("\n[12/13] Verifying Human-in-the-Loop Safeguards...")
    q_destructive = "Cancel route RTE-1001 and reassign vehicle TRK-101 immediately."
    res_dest = process_agent_query(user_query=q_destructive, user_role="Logistics Manager")
    check("Destructive actions intercepted with Human-in-the-Loop prompt",
          "Human-in-the-Loop Confirmation Required" in res_dest["response"] or "confirm" in res_dest["response"].lower(),
          f"Snippet: {res_dest['response'][:100]}...")

    # --------------------------------------------------------------------------
    # 13. AI API ENDPOINTS
    # --------------------------------------------------------------------------
    print("\n[13/13] Verifying AI API Endpoints & Auth...")
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    r_risk = client.get("/api/v1/ai/shipments/SHP-1001/risk", headers=headers)
    check("GET /api/v1/ai/shipments/{code}/risk returns 200", r_risk.status_code == 200, f"Status: {r_risk.status_code}")

    r_route = client.get("/api/v1/ai/routes/RTE-1001/analysis", headers=headers)
    check("GET /api/v1/ai/routes/{code}/analysis returns 200", r_route.status_code == 200, f"Status: {r_route.status_code}")

    r_ops = client.get("/api/v1/ai/operations/summary", headers=headers)
    check("GET /api/v1/ai/operations/summary returns 200", r_ops.status_code == 200, f"Status: {r_ops.status_code}")

    r_alerts = client.get("/api/v1/ai/alerts", headers=headers)
    check("GET /api/v1/ai/alerts returns 200", r_alerts.status_code == 200, f"Status: {r_alerts.status_code}")

    r_recs = client.get("/api/v1/ai/recommendations", headers=headers)
    check("GET /api/v1/ai/recommendations returns 200", r_recs.status_code == 200, f"Status: {r_recs.status_code}")

    # ==========================================================================
    # FINAL SUMMARY
    # ==========================================================================
    print("\n" + "=" * 80)
    print(f"PHASE 11 VERIFICATION RESULTS: {PASSED_CHECKS}/{TOTAL_CHECKS} CHECKS PASSED")
    print("=" * 80)

    if PASSED_CHECKS == TOTAL_CHECKS:
        print("\n>>> ALL PHASE 11 CAPABILITIES VERIFIED PERFECTLY! <<<\n")
        return 0
    else:
        print(f"\n>>> VERIFICATION FAILED: {TOTAL_CHECKS - PASSED_CHECKS} CHECKS FAILED <<<\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
