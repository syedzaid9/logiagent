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
    has_usable_password: bool = True
    has_activation_token: bool = False
    driver_id: Optional[int] = None
    driver_code: Optional[str] = None
    driver_name: Optional[str] = None
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

class ForgotPasswordRequest(BaseModel):
    email: str = Field(..., min_length=1, max_length=255)

class ForgotPasswordResponse(BaseModel):
    success: bool
    message: str
    reset_token: Optional[str] = None
    reset_url: Optional[str] = None

class ResetPasswordValidationResponse(BaseModel):
    valid: bool
    email: Optional[str] = None
    message: Optional[str] = None

class ResetPasswordRequest(BaseModel):
    token: str
    password: str = Field(..., min_length=6, max_length=128)

class ResetPasswordResponse(BaseModel):
    success: bool
    message: str

class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=1, max_length=128)
    new_password: str = Field(..., min_length=6, max_length=128)

class ChangePasswordResponse(BaseModel):
    success: bool
    message: str
