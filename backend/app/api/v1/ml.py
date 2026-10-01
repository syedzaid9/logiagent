from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.ml import (
    delay_predictor,
    eta_predictor,
    demand_forecaster,
    route_efficiency_analyzer,
    cost_optimizer,
    vehicle_utilization_calculator,
)
from app.models.vehicle import Vehicle

router = APIRouter(prefix="/ml", tags=["Machine Learning & Predictive Services"])

class DelayPredictRequest(BaseModel):
    distance_km: float
    current_delay_min: int = 0
    traffic_condition: str = "Moderate"
    weather_condition: str = "Clear"
    driver_hos_remaining: float = 11.0

class ETAPredictRequest(BaseModel):
    remaining_distance_km: float
    traffic_condition: str = "Moderate"
    weather_condition: str = "Clear"
    current_delay_min: int = 0

class RouteEfficiencyRequest(BaseModel):
    planned_distance_km: float
    actual_distance_km: float
    planned_duration_min: int
    actual_duration_min: int

@router.post("/predict-delay")
def predict_delay(
    req: DelayPredictRequest,
    current_user: User = Depends(get_current_user)
):
    return delay_predictor.predict_delay_risk(
        distance_km=req.distance_km,
        current_delay_min=req.current_delay_min,
        traffic_condition=req.traffic_condition,
        weather_condition=req.weather_condition,
        driver_hos_remaining=req.driver_hos_remaining
    )

@router.post("/predict-eta")
def predict_eta(
    req: ETAPredictRequest,
    current_user: User = Depends(get_current_user)
):
    return eta_predictor.predict_eta(
        current_time=datetime.utcnow(),
        remaining_distance_km=req.remaining_distance_km,
        traffic_condition=req.traffic_condition,
        weather_condition=req.weather_condition,
        current_delay_min=req.current_delay_min
    )

@router.get("/demand-forecast")
def get_demand_forecast(
    base_volume: int = 36,
    days_ahead: int = 7,
    current_user: User = Depends(get_current_user)
):
    return demand_forecaster.forecast_demand(base_volume=base_volume, days_ahead=days_ahead)

@router.post("/route-efficiency")
def analyze_route_efficiency(
    req: RouteEfficiencyRequest,
    current_user: User = Depends(get_current_user)
):
    return route_efficiency_analyzer.analyze_route(
        planned_distance_km=req.planned_distance_km,
        actual_distance_km=req.actual_distance_km,
        planned_duration_min=req.planned_duration_min,
        actual_duration_min=req.actual_duration_min
    )

@router.get("/vehicle-utilization")
def get_vehicle_utilization(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    vehicles = db.query(Vehicle).all()
    v_dicts = [
        {"type": v.type, "max_capacity_kg": v.max_capacity_kg, "current_load_kg": v.current_load_kg, "status": v.status}
        for v in vehicles
    ]
    return vehicle_utilization_calculator.calculate_utilization(v_dicts)
