import pytest
from app.agents import process_agent_query

def test_scenario_1_shipment_tracking():
    query = "Where is shipment SHP-1001?"
    res = process_agent_query(user_query=query, user_role="Logistics Manager")
    assert "SHP-1001" in res["response"]
    assert len(res["actions_performed"]) > 0
    assert "shipment_tracking_tool" in res["tools_used"]
    assert res["structured_data"] is not None

def test_scenario_2_delayed_shipments():
    query = "Show all delayed shipments."
    res = process_agent_query(user_query=query, user_role="Dispatcher")
    assert "Delayed" in res["response"] or "Delay" in res["response"]
    assert "delay_detection_tool" in res["tools_used"]
    assert len(res["actions_performed"]) > 0

def test_scenario_3_vehicle_availability():
    query = "Which vehicle is available for a 1500 kg shipment?"
    res = process_agent_query(user_query=query, user_role="Dispatcher")
    assert "Available" in res["response"] or "Vehicle" in res["response"]
    assert "vehicle_availability_tool" in res["tools_used"]

def test_scenario_4_route_optimization():
    query = "Find the fastest route for SHP-1001."
    res = process_agent_query(user_query=query, user_role="Logistics Manager")
    assert "Route" in res["response"] or "Corridor" in res["response"] or "km" in res["response"]
    assert "route_optimization_tool" in res["tools_used"]

def test_scenario_5_delay_root_cause():
    query = "Why is SHP-1001 likely to be delayed?"
    res = process_agent_query(user_query=query, user_role="Operations Team")
    assert "Delay" in res["response"] or "Risk" in res["response"]
    assert "delay_detection_tool" in res["tools_used"] or "route_optimization_tool" in res["tools_used"]

def test_scenario_6_rag_failed_delivery_policy():
    query = "What is the failed delivery policy?"
    res = process_agent_query(user_query=query, user_role="Operations Team")
    assert "SOP-LOG-02" in res["response"] or "Failed Delivery" in res["response"] or "policy" in res["response"].lower()
    assert len(res["sources"]) > 0
    assert any("SOP-LOG-02" in s["document_code"] for s in res["sources"])

def test_scenario_7_fleet_performance():
    query = "How is our fleet performing this month?"
    res = process_agent_query(user_query=query, user_role="Logistics Manager")
    assert "Performance" in res["response"] or "Utilization" in res["response"] or "SLA" in res["response"]
    assert "logistics_analytics_tool" in res["tools_used"]
