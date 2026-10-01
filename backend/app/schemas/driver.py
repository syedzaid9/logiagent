from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime

class DriverBase(BaseModel):
    driver_code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    email: str = Field(..., min_length=1, max_length=255)
    phone: str = Field(..., min_length=1, max_length=50)
    license_number: str = Field(..., min_length=1, max_length=50)
    license_type: str = Field(default="CDL-A", max_length=50) # CDL-A, CDL-B, Standard
    status: str = Field(default="Available", max_length=50) # Available, Assigned, On Duty, Off Duty, Rest, Deactivated
    rating: float = Field(default=4.8, ge=0.0, le=5.0)
    hours_of_service_remaining: float = Field(default=11.0, ge=0.0, le=14.0) # DOT regulations
    current_vehicle_id: Optional[int] = None
    current_latitude: Optional[float] = Field(None, ge=-90.0, le=90.0)
    current_longitude: Optional[float] = Field(None, ge=-180.0, le=180.0)

class DriverCreate(DriverBase):
    pass

class DriverUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    license_number: Optional[str] = Field(None, max_length=50)
    license_type: Optional[str] = Field(None, max_length=50)
    status: Optional[str] = Field(None, max_length=50)
    rating: Optional[float] = Field(None, ge=0.0, le=5.0)
    hours_of_service_remaining: Optional[float] = Field(None, ge=0.0, le=14.0)
    current_vehicle_id: Optional[int] = None
    current_latitude: Optional[float] = Field(None, ge=-90.0, le=90.0)
    current_longitude: Optional[float] = Field(None, ge=-180.0, le=180.0)

class DriverResponse(DriverBase):
    id: int
    assigned_vehicle_code: Optional[str] = None
    assigned_vehicle_model: Optional[str] = None
    assigned_vehicle_type: Optional[str] = None
    assigned_vehicle_location: Optional[str] = None
    active_shipment_code: Optional[str] = None
    active_shipment_id: Optional[int] = None
    active_shipment_status: Optional[str] = None
    active_shipment_origin: Optional[str] = None
    active_shipment_destination: Optional[str] = None
    active_shipment_weight_kg: Optional[float] = None
    completed_deliveries_count: int = 0
    active_deliveries_count: int = 0
    hos_compliance_status: str = "Compliant"
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class DriverStatsResponse(BaseModel):
    total_drivers: int
    available_drivers: int
    assigned_drivers: int
    on_duty_drivers: int
    off_duty_drivers: int
    rest_drivers: int
    deactivated_drivers: int
    average_hos_remaining: float
    average_rating: float
    drivers_with_active_shipments: int

