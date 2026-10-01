import pytest
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

def test_shipment_tracking_tool():
    res = shipment_tracking_tool.execute(shipment_code="SHP-1001")
    assert res["found"] is True
    assert res["shipment_code"] == "SHP-1001"
    assert "status" in res
    assert "origin" in res
    assert "destination" in res

def test_vehicle_availability_tool():
    res = vehicle_availability_tool.execute(min_capacity_kg=1500.0)
    assert "available_vehicles_count" in res
    assert res["available_vehicles_count"] > 0
    assert len(res["vehicles"]) > 0
    for v in res["vehicles"]:
        assert v["available_capacity_kg"] >= 1500.0

def test_driver_management_tool():
    res = driver_management_tool.execute(available_only=True)
    assert res["count"] > 0
    assert len(res["drivers"]) > 0

def test_route_optimization_tool():
    res = route_optimization_tool.execute(shipment_code="SHP-1001")
    assert res["success"] is True
    assert "recommended_route" in res
    assert res["recommended_route"]["distance_km"] > 0
    assert len(res["stops"]) > 0

def test_eta_calculation_tool():
    res = eta_calculation_tool.execute(shipment_code="SHP-1001")
    assert res["success"] is True
    assert "calculated_eta" in res
    assert "delay_minutes" in res

def test_delay_detection_tool():
    res = delay_detection_tool.execute(min_delay_minutes=0)
    assert res["success"] is True
    assert "delayed_shipments" in res
    assert res["delayed_count"] > 0

def test_cost_calculation_tool():
    res = cost_calculation_tool.execute(shipment_code="SHP-1001")
    assert res["success"] is True
    assert "total_cost_usd" in res or "total_cost" in res

def test_logistics_analytics_tool():
    res = logistics_analytics_tool.execute()
    assert res["success"] is True
    assert "performance_summary" in res
    assert "fleet_utilization" in res

def test_notification_tool():
    res = notification_tool.execute(
        title="Test Alert",
        message="Automated unit test alert",
        notification_type="delay",
        channel="In-App",
        recipient="test@logiagent.io"
    )
    assert res["success"] is True
    assert res["notification_id"] > 0
