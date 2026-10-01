import pytest
from datetime import datetime
from app.ml import (
    delay_predictor,
    eta_predictor,
    demand_forecaster,
    route_efficiency_analyzer,
    cost_optimizer,
    vehicle_utilization_calculator,
)

def test_delay_predictor():
    res = delay_predictor.predict_delay_risk(
        distance_km=450.0,
        current_delay_min=45,
        traffic_condition="Heavy",
        weather_condition="Rain"
    )
    assert res["risk_score"] > 50.0
    assert res["risk_level"] in ["High", "Critical"]
    assert len(res["important_factors"]) > 0

def test_eta_predictor():
    now = datetime.utcnow()
    res = eta_predictor.predict_eta(
        current_time=now,
        remaining_distance_km=300.0,
        traffic_condition="Moderate"
    )
    assert res["total_duration_minutes"] > 0
    assert "formatted_eta" in res

def test_demand_forecaster():
    forecast = demand_forecaster.forecast_demand(base_volume=35, days_ahead=7)
    assert len(forecast) == 7
    for f in forecast:
        assert f["predicted_shipments"] > 0
        assert f["lower_bound"] <= f["predicted_shipments"] <= f["upper_bound"]

def test_route_efficiency_analyzer():
    res = route_efficiency_analyzer.analyze_route(
        planned_distance_km=500.0,
        actual_distance_km=520.0,
        planned_duration_min=400,
        actual_duration_min=415
    )
    assert res["efficiency_score"] > 80.0
    assert res["detour_detected"] is False

def test_cost_optimizer():
    cost = cost_optimizer.calculate_trip_cost(distance_km=500.0, vehicle_type="Semi-Truck (Dry Van)")
    assert cost["total_cost"] > 0
    assert cost["cost_per_km"] > 1.0
