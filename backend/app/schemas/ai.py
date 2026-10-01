from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

class AlertResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    alert_code: str
    alert_type: str
    severity: str
    entity_type: str
    entity_id: str
    title: str
    message: str
    evidence: Optional[str] = None
    recommended_action: Optional[str] = None
    status: str
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[str] = None
    resolved_at: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class AlertAcknowledgeRequest(BaseModel):
    notes: Optional[str] = Field(None, max_length=500)

class AlertResolveRequest(BaseModel):
    resolution_summary: Optional[str] = Field(None, max_length=1000)

class RiskFactorItem(BaseModel):
    factor: str
    impact: str
    detail: str

class RecommendedActionItem(BaseModel):
    priority: str
    action: str
    requires_confirmation: bool = False

class ShipmentRiskResponse(BaseModel):
    shipment_id: Optional[int] = None
    shipment_code: str
    prediction_status: str = "success"
    status: Optional[str] = None
    origin: Optional[str] = None
    destination: Optional[str] = None
    risk_level: str = "LOW"
    risk_score: float = Field(..., ge=0.0, le=100.0)
    delay_probability: float = Field(..., ge=0.0, le=1.0)
    predicted_delay_minutes: int = 0
    predicted_eta: Optional[str] = None
    formatted_eta: Optional[str] = None
    deadline_eta: Optional[str] = None
    is_deadline_at_risk: bool = False
    traffic_condition: Optional[str] = None
    weather_condition: Optional[str] = None
    driver_name: Optional[str] = None
    vehicle_code: Optional[str] = None
    risk_factors: List[RiskFactorItem] = []
    recommended_actions: List[RecommendedActionItem] = []
    error: Optional[str] = None

class RouteCorridorDetail(BaseModel):
    distance_km: float = 0.0
    duration_minutes: int = 0
    estimated_cost_usd: float = 0.0
    traffic_condition: Optional[str] = None
    weather_condition: Optional[str] = None

class RouteAnalysisResponse(BaseModel):
    success: bool
    route_code: Optional[str] = None
    status: Optional[str] = "Planned"
    primary_corridor: Dict[str, Any] = {}
    alternative_corridor: Dict[str, Any] = {}
    cost_comparison: Dict[str, Any] = {}
    optimization_summary: Optional[str] = None

class AIRecommendationItem(BaseModel):
    id: str
    priority: str
    category: str
    entity_type: str
    entity_code: str
    problem: str
    evidence: List[str]
    recommended_action: str
    requires_human_confirmation: bool
    action_type: str
    action_payload: Dict[str, Any]
    expected_effect: str

class OperationalSummaryResponse(BaseModel):
    total_active_shipments: int
    high_risk_shipments_count: int
    active_alerts_count: int
    critical_alerts_count: int
    fleet_utilization_pct: float
    risk_distribution: Dict[str, int]
    top_recommendations: List[AIRecommendationItem] = []
