from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime

class UserBase(BaseModel):
    email: str = Field(..., min_length=1, max_length=255)
    full_name: str = Field(..., min_length=1, max_length=255)
    role: str = Field(default="Driver", max_length=50) # Admin, Logistics Manager, Dispatcher, Driver, Operations Team

class UserCreate(UserBase):
    password: str = Field(..., min_length=3, max_length=128)

class UserLogin(BaseModel):
    email: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=1, max_length=128)

class UserResponse(UserBase):
    id: int
    is_active: bool
    account_status: str = "Active"
    approval_status: str = "Approved"
    driver_id: Optional[int] = None
    driver_code: Optional[str] = None
    driver_phone: Optional[str] = None
    assigned_vehicle_id: Optional[int] = None
    assigned_vehicle_code: Optional[str] = None
    permissions: List[str] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
