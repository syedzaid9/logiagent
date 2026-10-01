from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime

class VehicleBase(BaseModel):
    vehicle_code: str = Field(..., min_length=1, max_length=50)
    model: str = Field(..., min_length=1, max_length=100)
    type: str = Field(..., max_length=50) # Semi-Truck (Dry Van), Reefer, Flatbed, Box Truck, Sprinter Van
    max_capacity_kg: float = Field(..., gt=0.0, le=100000.0)
    current_load_kg: float = Field(default=0.0, ge=0.0, le=100000.0)
    max_volume_m3: float = Field(default=80.0, gt=0.0, le=500.0)
    current_volume_m3: float = Field(default=0.0, ge=0.0, le=500.0)
    status: str = Field(default="Available", max_length=50) # Available, Assigned, In Transit, Maintenance
    current_location: str = Field(default="Central Distribution Hub", max_length=255)
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    fuel_level_pct: float = Field(default=100.0, ge=0.0, le=100.0)
    fuel_type: str = Field(default="Diesel", max_length=50) # Diesel, Electric, Hybrid
    mileage_km: float = Field(default=45000.0, ge=0.0)
    driver_id: Optional[int] = None

class VehicleCreate(VehicleBase):
    pass

class VehicleUpdate(BaseModel):
    model: Optional[str] = Field(None, max_length=100)
    type: Optional[str] = Field(None, max_length=50)
    max_capacity_kg: Optional[float] = Field(None, gt=0.0, le=100000.0)
    max_volume_m3: Optional[float] = Field(None, gt=0.0, le=500.0)
    current_load_kg: Optional[float] = Field(None, ge=0.0, le=100000.0)
    current_volume_m3: Optional[float] = Field(None, ge=0.0, le=500.0)
    status: Optional[str] = Field(None, max_length=50)
    current_location: Optional[str] = Field(None, max_length=255)
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0)
    fuel_level_pct: Optional[float] = Field(None, ge=0.0, le=100.0)
    fuel_type: Optional[str] = Field(None, max_length=50)
    mileage_km: Optional[float] = Field(None, ge=0.0)
    driver_id: Optional[int] = None

class VehicleResponse(VehicleBase):
    id: int
    utilization_pct: float = 0.0
    available_capacity_kg: float = 0.0
    available_volume_m3: float = 0.0
    driver_name: Optional[str] = None
    driver_code: Optional[str] = None
    driver_phone: Optional[str] = None
    active_shipment_code: Optional[str] = None
    active_shipment_id: Optional[int] = None
    active_shipment_status: Optional[str] = None
    active_shipment_weight_kg: Optional[float] = None
    origin_hub: Optional[str] = None
    destination_hub: Optional[str] = None
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class FleetStatsResponse(BaseModel):
    total_vehicles: int
    available_vehicles: int
    assigned_vehicles: int
    in_transit_vehicles: int
    maintenance_vehicles: int
    average_utilization_pct: float
    total_fleet_capacity_kg: float
    total_fleet_load_kg: float
