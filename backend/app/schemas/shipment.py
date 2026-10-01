from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime

class LocationSimple(BaseModel):
    id: int
    name: str
    city: str
    state: str
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)

    model_config = ConfigDict(from_attributes=True)

class ShipmentHistoryResponse(BaseModel):
    id: int
    shipment_id: int
    status: str
    location_name: Optional[str] = None
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0)
    notes: Optional[str] = None
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)

class ShipmentBase(BaseModel):
    shipment_code: str = Field(..., min_length=1, max_length=50)
    order_id: Optional[int] = None
    customer_id: int
    origin_id: int
    destination_id: int
    vehicle_id: Optional[int] = None
    driver_id: Optional[int] = None
    status: str = Field(default="Pending", max_length=50)
    cargo_type: str = Field(default="General Freight", max_length=100)
    weight_kg: float = Field(default=1000.0, gt=0.0, le=100000.0)
    volume_m3: float = Field(default=10.0, gt=0.0, le=500.0)
    temperature_controlled: bool = False
    target_temp_celsius: Optional[float] = Field(None, ge=-50.0, le=50.0)
    pickup_time: Optional[datetime] = None
    expected_delivery: datetime
    actual_delivery: Optional[datetime] = None
    estimated_eta: Optional[datetime] = None
    delay_minutes: int = Field(default=0, ge=0)
    delay_reason: Optional[str] = Field(None, max_length=255)
    delay_risk_score: float = Field(default=0.0, ge=0.0, le=100.0)
    delay_risk_level: str = Field(default="Low", max_length=50)
    special_instructions: Optional[str] = None

class ShipmentCreate(ShipmentBase):
    pass

class ShipmentUpdate(BaseModel):
    status: Optional[str] = Field(None, max_length=50)
    vehicle_id: Optional[int] = None
    driver_id: Optional[int] = None
    current_latitude: Optional[float] = Field(None, ge=-90.0, le=90.0)
    current_longitude: Optional[float] = Field(None, ge=-180.0, le=180.0)
    current_location_name: Optional[str] = None
    delay_minutes: Optional[int] = None
    delay_reason: Optional[str] = None
    estimated_eta: Optional[datetime] = None
    actual_delivery: Optional[datetime] = None
    special_instructions: Optional[str] = None
    notes: Optional[str] = None

class ShipmentResponse(ShipmentBase):
    id: int
    current_latitude: Optional[float] = None
    current_longitude: Optional[float] = None
    current_location_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    # Extra joined fields for rich UI
    customer_name: Optional[str] = None
    origin_name: Optional[str] = None
    origin_city: Optional[str] = None
    origin_state: Optional[str] = None
    destination_name: Optional[str] = None
    destination_city: Optional[str] = None
    destination_state: Optional[str] = None
    vehicle_code: Optional[str] = None
    driver_name: Optional[str] = None
    cost_total_usd: Optional[float] = None
    cost_breakdown: Optional[dict] = None
    history: Optional[List[ShipmentHistoryResponse]] = None

    model_config = ConfigDict(from_attributes=True)
