from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class KPISummary(BaseModel):
    total_shipments: int
    in_transit_shipments: int
    delivered_shipments: int
    delayed_shipments: int
    at_risk_shipments: int
    available_vehicles: int
    active_vehicles: int
    total_vehicles: int
    fleet_utilization_pct: float
    today_deliveries_count: int
    average_eta_hours: float
    total_transportation_cost: float
    on_time_delivery_rate_pct: float

class StatusBreakdown(BaseModel):
    status: str
    count: int
    percentage: float

class VehicleTypeUtilization(BaseModel):
    vehicle_type: str
    total_count: int
    active_count: int
    average_load_pct: float

class DelayRootCause(BaseModel):
    reason: str
    count: int
    percentage: float

class CostBreakdown(BaseModel):
    category: str
    amount: float
    percentage: float

class DemandForecastPoint(BaseModel):
    date: str
    predicted_shipments: int
    lower_bound: int
    upper_bound: int

class AnalyticsDashboardResponse(BaseModel):
    kpis: KPISummary
    status_distribution: List[StatusBreakdown]
    vehicle_utilization: List[VehicleTypeUtilization]
    delay_root_causes: List[DelayRootCause]
    cost_breakdown: List[CostBreakdown]
    demand_forecast: List[DemandForecastPoint]
    recent_activity: List[Dict[str, Any]]
