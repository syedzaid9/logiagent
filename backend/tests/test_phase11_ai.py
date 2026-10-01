import pytest
from datetime import datetime, timezone, timedelta
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

@pytest.fixture(scope="module")
def admin_token():
    res = client.post("/api/v1/auth/login", json={"email": "admin@logiagent.io", "password": "LogiAgent2026!"})
    assert res.status_code == 200
    return res.json()["access_token"]

@pytest.fixture(scope="module")
def driver_token():
    res = client.post("/api/v1/auth/login", json={"email": "driver@logiagent.io", "password": "LogiAgent2026!"})
    assert res.status_code == 200
    return res.json()["access_token"]


# ==============================================================================
# 1. ETA PREDICTION TESTS
# ==============================================================================

def test_eta_predictor_calculation():
    """Verify core ETA prediction engine accounts for speed, traffic, and mandatory rest stops."""
    now_dt = datetime.now(timezone.utc)
    res = eta_predictor.predict_eta(
        current_time=now_dt,
        remaining_distance_km=700.0,
        traffic_condition="Moderate",
        weather_condition="Clear",
        current_delay_min=15
    )
    assert "predicted_eta" in res
    assert res["effective_speed_kmh"] > 0
    assert res["total_duration_minutes"] > 0
    assert res["rest_stop_minutes"] >= 30 # Over 4.5h driving requires rest stop

def test_eta_prediction_service_valid_shipment():
    """Verify shipment_risk_service computes standardized ETA for existing shipment."""
    db = SessionLocal()
    try:
        res = shipment_risk_service.predict_eta(db, "SHP-1001")
        assert res["prediction_status"] == "success"
        assert res["predicted_eta"] is not None
        assert "formatted_eta" in res
    finally:
        db.close()

def test_eta_prediction_invalid_shipment_returns_unavailable():
    """Verify service returns prediction_unavailable rather than crashing or inventing data."""
    db = SessionLocal()
    try:
        res = shipment_risk_service.predict_eta(db, "SHP-NONEXISTENT-999")
        assert res["prediction_status"] == "prediction_unavailable"
        assert res["predicted_eta"] is None
    finally:
        db.close()


# ==============================================================================
# 2. DELAY PREDICTION & RISK SCORING TESTS
# ==============================================================================

def test_delay_predictor_risk_classification():
    """Verify ML delay predictor produces bounded scores and explainable factors."""
    res_low = delay_predictor.predict_delay_risk(
        distance_km=100.0,
        current_delay_min=0,
        traffic_condition="Light",
        weather_condition="Clear",
        driver_hos_remaining=10.0
    )
    assert res_low["risk_level"] in ["Low", "Medium"]
    assert res_low["risk_score"] <= 35.0

    res_crit = delay_predictor.predict_delay_risk(
        distance_km=900.0,
        current_delay_min=60,
        traffic_condition="Severe Congestion",
        weather_condition="Storm",
        driver_hos_remaining=2.0
    )
    assert res_crit["risk_level"] in ["High", "Critical"]
    assert res_crit["risk_score"] >= 75.0
    assert len(res_crit["important_factors"]) >= 3

def test_delay_prediction_service_valid_shipment():
    """Verify delay prediction service exposes probability and factors."""
    db = SessionLocal()
    try:
        res = shipment_risk_service.predict_delay(db, "SHP-1001")
        assert res["prediction_status"] == "success"
        assert 0.0 <= res["delay_probability"] <= 1.0
        assert res["risk_level"] in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        assert len(res["important_features"]) > 0
    finally:
        db.close()


# ==============================================================================
# 3. TRANSPORTATION COST PREDICTION TESTS
# ==============================================================================

def test_cost_service_estimate_shipment_cost():
    """Verify cost calculation breakdown parity."""
    db = SessionLocal()
    try:
        res = cost_service.estimate_shipment_cost(db, "SHP-1001")
        assert res["success"] is True
        assert res["total_cost_usd"] > 0
        assert res["cost_per_km"] > 0
        assert "fuel_cost" in res["cost_breakdown"]
        assert "driver_cost" in res["cost_breakdown"]
    finally:
        db.close()

def test_cost_service_route_comparison():
    """Verify corridor cost comparison logic."""
    res = cost_service.compare_route_costs(
        primary_distance_km=1800.0,
        alternative_distance_km=1950.0,
        primary_toll_fees=25.0,
        alternative_toll_fees=0.0
    )
    assert res["success"] is True
    assert "cost_difference_usd" in res
    assert "recommendation" in res


# ==============================================================================
# 4. UNIFIED SHIPMENT RISK ENGINE TESTS
# ==============================================================================

def test_shipment_risk_service_complete_analysis():
    """Verify comprehensive risk evaluation combines live telemetry and ML outputs."""
    db = SessionLocal()
    try:
        res = shipment_risk_service.analyze_shipment_risk(db, "SHP-1001")
        assert res["prediction_status"] == "success"
        assert res["shipment_code"] == "SHP-1001"
        assert res["risk_level"] in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        assert 0.0 <= res["delay_probability"] <= 1.0
        assert len(res["risk_factors"]) > 0
        assert len(res["recommended_actions"]) > 0
    finally:
        db.close()

def test_driver_cannot_query_unassigned_shipment_risk():
    """Verify Driver role data scoping in risk service."""
    db = SessionLocal()
    try:
        driver_ctx = {"role": "DRIVER", "driver_id": 999} # Driver with non-matching ID
        res = shipment_risk_service.analyze_shipment_risk(db, "SHP-1001", user_context=driver_ctx)
        assert res["prediction_status"] == "prediction_unavailable"
        assert "Unauthorized" in res["error"]
    finally:
        db.close()


# ==============================================================================
# 5. OPERATIONAL ANOMALY DETECTION & ALERT TESTS
# ==============================================================================

def test_anomaly_detection_scan_and_generation():
    """Verify proactive anomaly scan generates structured alerts."""
    db = SessionLocal()
    try:
        scan_res = anomaly_detection_service.scan_and_generate_alerts(db)
        assert scan_res["success"] is True
        assert scan_res["active_anomalies_detected"] >= 0
    finally:
        db.close()

def test_alert_deduplication():
    """Verify that running consecutive scans does not duplicate active alerts."""
    db = SessionLocal()
    try:
        anomaly_detection_service.scan_and_generate_alerts(db)
        count_1 = db.query(Alert).filter(Alert.status == "active").count()

        # Second immediate scan
        anomaly_detection_service.scan_and_generate_alerts(db)
        count_2 = db.query(Alert).filter(Alert.status == "active").count()

        assert count_1 == count_2, "Alert deduplication failed: duplicate active alerts were created"
    finally:
        db.close()

def test_alert_lifecycle_acknowledge_and_resolve():
    """Verify alert status transition from active -> acknowledged -> resolved."""
    db = SessionLocal()
    try:
        # Create a dedicated test alert
        test_alert = Alert(
            alert_code=f"ALT-TST-{int(datetime.now().timestamp())}",
            alert_type="HIGH_DELAY_RISK",
            severity="HIGH",
            entity_type="shipment",
            entity_id="SHP-TEST-ALERT",
            title="Test Delay Alert",
            message="Test alert message",
            status="active",
            created_at=datetime.now(timezone.utc)
        )
        db.add(test_alert)
        db.commit()
        db.refresh(test_alert)

        # 1. Acknowledge
        ack = anomaly_detection_service.acknowledge_alert(db, test_alert.id, "operator@logiagent.io")
        assert ack is not None
        assert ack.status == "acknowledged"
        assert ack.acknowledged_by == "operator@logiagent.io"

        # 2. Resolve
        res = anomaly_detection_service.resolve_alert(db, test_alert.id, "operator@logiagent.io")
        assert res is not None
        assert res.status == "resolved"
        assert res.resolved_at is not None

        # Clean up
        db.delete(test_alert)
        db.commit()
    finally:
        db.close()


# ==============================================================================
# 6. OPERATIONAL RECOMMENDATIONS & HUMAN-IN-THE-LOOP TESTS
# ==============================================================================

def test_recommendation_service_generation():
    """Verify operational recommendation engine produces prioritized advice."""
    db = SessionLocal()
    try:
        recs = recommendation_service.generate_recommendations(db, limit=5)
        assert isinstance(recs, list)
        if recs:
            r = recs[0]
            assert "priority" in r
            assert "category" in r
            assert "problem" in r
            assert "recommended_action" in r
            assert "requires_human_confirmation" in r
    finally:
        db.close()

def test_human_in_the_loop_confirmation_guardrail():
    """Verify agent intercepts destructive requests and prompts for human confirmation."""
    query = "Cancel route RT-1001 immediately."
    res = process_agent_query(user_query=query, user_role="Logistics Manager")
    assert "Human-in-the-Loop Confirmation Required" in res["response"]
    assert "confirm" in res["response"].lower() or "safeguard" in res["response"].lower()


# ==============================================================================
# 7. ROLE-AWARE NATURAL LANGUAGE AI ANALYST TESTS
# ==============================================================================

def test_agent_at_risk_shipments_query():
    """Verify natural-language query: 'Which shipments are at risk today?'."""
    query = "Which shipments are at risk today?"
    res = process_agent_query(user_query=query, user_role="Logistics Manager")
    assert "shipment_risk_tool" in res["tools_used"] or "delay_detection_tool" in res["tools_used"]
    assert "Risk" in res["response"] or "Schedule" in res["response"]

def test_agent_operational_problems_query():
    """Verify natural-language query: 'What are the biggest operational problems today?'."""
    query = "What are the biggest operational problems today?"
    res = process_agent_query(user_query=query, user_role="Logistics Manager")
    assert "anomaly_alerts_tool" in res["tools_used"]
    assert "Operational" in res["response"] or "Alerts" in res["response"] or "Optimal" in res["response"]

def test_agent_explain_shipment_delay_query():
    """Verify natural-language explainable risk: 'Why is shipment SHP-1001 delayed?'."""
    query = "Why is shipment SHP-1001 delayed?"
    res = process_agent_query(user_query=query, user_role="Operations Team")
    assert "SHP-1001" in res["response"]
    assert "Contributing" in res["response"] or "Risk" in res["response"] or "Status" in res["response"]

def test_agent_route_comparison_query():
    """Verify natural-language query: 'Compare the current route with the optimized route.'."""
    query = "Compare the current route with the optimized route for SHP-1001"
    res = process_agent_query(user_query=query, user_role="Logistics Manager")
    assert "route_intelligence_tool" in res["tools_used"] or "route_optimization_tool" in res["tools_used"]
    assert "Corridor" in res["response"] or "km" in res["response"] or "Cost" in res["response"]

def test_agent_underutilized_fleet_query():
    """Verify natural-language query: 'Which vehicles are underutilized?'."""
    query = "Which vehicles are underutilized?"
    res = process_agent_query(user_query=query, user_role="Fleet Manager")
    assert "vehicle_availability_tool" in res["tools_used"] or "anomaly_alerts_tool" in res["tools_used"]
    assert "Fleet" in res["response"] or "Capacity" in res["response"] or "Vehicle" in res["response"]

def test_agent_driver_workload_query():
    """Verify natural-language query: 'Which drivers have the highest workload?'."""
    query = "Which drivers have the highest workload?"
    res = process_agent_query(user_query=query, user_role="Dispatcher")
    assert "driver_management_tool" in res["tools_used"]
    assert "Driver" in res["response"] or "HOS" in res["response"]

def test_agent_delivery_performance_query():
    """Verify natural-language query: 'How many shipments were delivered this week?'."""
    query = "How many shipments were delivered this week?"
    res = process_agent_query(user_query=query, user_role="Logistics Manager")
    assert "logistics_analytics_tool" in res["tools_used"]
    assert "Delivery" in res["response"] or "Shipments" in res["response"]


# ==============================================================================
# 8. AI API ENDPOINT TESTS
# ==============================================================================

def test_api_shipment_risk_endpoint(admin_token):
    """Verify GET /api/v1/ai/shipments/{code}/risk endpoint."""
    res = client.get("/api/v1/ai/shipments/SHP-1001/risk", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200
    data = res.json()
    assert data["shipment_code"] == "SHP-1001"
    assert "risk_score" in data
    assert "delay_probability" in data
    assert "risk_factors" in data

def test_api_route_analysis_endpoint(admin_token):
    """Verify GET /api/v1/ai/routes/{code}/analysis endpoint."""
    res = client.get("/api/v1/ai/routes/RTE-1001/analysis", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200
    data = res.json()
    assert data["route_code"] == "RTE-1001"
    assert "primary_corridor" in data
    assert "cost_comparison" in data

    # Verify 404 on non-existent route
    res_404 = client.get("/api/v1/ai/routes/RTE-NONEXISTENT/analysis", headers={"Authorization": f"Bearer {admin_token}"})
    assert res_404.status_code == 404

def test_api_operations_summary_endpoint(admin_token):
    """Verify GET /api/v1/ai/operations/summary endpoint."""
    res = client.get("/api/v1/ai/operations/summary", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200
    data = res.json()
    assert "total_active_shipments" in data
    assert "fleet_utilization_pct" in data
    assert "risk_distribution" in data
    assert "top_recommendations" in data

def test_api_alerts_list_and_acknowledge(admin_token):
    """Verify GET /api/v1/ai/alerts and acknowledge workflow."""
    res = client.get("/api/v1/ai/alerts", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200
    alerts = res.json()
    assert isinstance(alerts, list)

    if alerts:
        a_id = alerts[0]["id"]
        ack_res = client.post(f"/api/v1/ai/alerts/{a_id}/acknowledge", headers={"Authorization": f"Bearer {admin_token}"})
        assert ack_res.status_code == 200
        assert ack_res.json()["status"] in ["acknowledged", "resolved"]
