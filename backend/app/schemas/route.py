from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Any
from datetime import datetime

class Waypoint(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    location: Optional[str] = Field(None, max_length=255)
    lat: float = Field(..., ge=-90.0, le=90.0)
    lng: float = Field(..., ge=-180.0, le=180.0)
    type: str = Field(default="Waypoint", max_length=50) # Origin, Waypoint, Fuel & Rest, Inspection, Destination
    estimated_arrival: Optional[str] = Field(None, max_length=100)

class RouteCreate(BaseModel):
    route_code: Optional[str] = Field(None, max_length=50)
    origin_id: int
    destination_id: int
    shipment_id: Optional[int] = None
    vehicle_id: Optional[int] = None
    driver_id: Optional[int] = None
    traffic_condition: str = Field(default="Moderate", max_length=50)
    weather_condition: str = Field(default="Clear", max_length=50)
    priority: str = Field(default="fastest", max_length=50)

class RouteUpdate(BaseModel):
    destination_id: Optional[int] = None
    shipment_id: Optional[int] = None
    vehicle_id: Optional[int] = None
    driver_id: Optional[int] = None
    traffic_condition: Optional[str] = Field(None, max_length=50)
    weather_condition: Optional[str] = Field(None, max_length=50)
    actual_distance_km: Optional[float] = Field(None, ge=0.0)
    actual_duration_min: Optional[int] = Field(None, ge=0)
    status: Optional[str] = Field(None, max_length=50) # Planned, Assigned, In Transit, Delayed, Completed, Cancelled

class RouteCalculateRequest(BaseModel):
    origin_id: int
    destination_id: int
    shipment_id: Optional[int] = None
    vehicle_id: Optional[int] = None
    driver_id: Optional[int] = None
    avoid_tolls: bool = False
    priority: str = Field(default="fastest", max_length=50) # fastest, shortest, lowest_cost

class RouteOptimizeRequest(BaseModel):
    route_code: Optional[str] = Field(None, max_length=50)
    shipment_code: Optional[str] = Field(None, max_length=50)
    priority: str = Field(default="fastest", max_length=50) # fastest, shortest, lowest_cost
    apply_optimization: bool = False

class RouteStatsResponse(BaseModel):
    total_routes: int
    active_routes: int
    planned_routes: int
    completed_routes: int
    delayed_routes: int
    average_distance_km: float
    average_duration_min: int
    average_efficiency_pct: float
    total_network_distance_km: float

class RouteResponse(BaseModel):
    id: Optional[int] = None
    route_code: str
    status: str = "Planned" # Planned, Assigned, In Transit, Delayed, Completed, Cancelled
    shipment_id: Optional[int] = None
    shipment_code: Optional[str] = None
    shipment_status: Optional[str] = None
    cargo_type: Optional[str] = None
    weight_kg: Optional[float] = None
    customer_name: Optional[str] = None
    origin_id: int
    origin_code: Optional[str] = None
    origin_name: str
    origin_city: str
    origin_state: str
    origin_lat: float
    origin_lng: float
    destination_id: int
    destination_code: Optional[str] = None
    destination_name: str
    destination_city: str
    destination_state: str
    destination_lat: float
    destination_lng: float
    vehicle_id: Optional[int] = None
    vehicle_code: Optional[str] = None
    vehicle_model: Optional[str] = None
    vehicle_type: Optional[str] = None
    vehicle_status: Optional[str] = None
    driver_id: Optional[int] = None
    driver_code: Optional[str] = None
    driver_name: Optional[str] = None
    driver_phone: Optional[str] = None
    driver_hos_remaining: Optional[float] = None
    planned_distance_km: float
    actual_distance_km: Optional[float] = None
    planned_duration_min: int
    actual_duration_min: Optional[int] = None
    traffic_condition: str = "Moderate"
    weather_condition: str = "Clear"
    estimated_cost: float = 0.0
    cost_total_usd: Optional[float] = None
    cost_per_km: Optional[float] = None
    fuel_cost: Optional[float] = None
    driver_cost: Optional[float] = None
    toll_cost: Optional[float] = None
    maintenance_cost: Optional[float] = None
    eta_projection: Optional[str] = None
    delay_minutes: int = 0
    waypoints: List[Waypoint] = []
    polyline: List[List[float]] = []
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
