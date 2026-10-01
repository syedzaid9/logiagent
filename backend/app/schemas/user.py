from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from app.schemas.auth import UserResponse

class UserProvisionRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=255)
    role: str = Field(default="Driver", max_length=50)  # Admin, Logistics Manager, Dispatcher, Fleet Manager, Driver, Analyst
    driver_id: Optional[int] = None
    auto_approve: bool = False
    require_approval: Optional[bool] = None

class UserProvisionResponse(BaseModel):
    success: bool
    message: str
    user: UserResponse
    activation_token: Optional[str] = None
    requires_approval: bool = False

class UserUpdateRequest(BaseModel):
    full_name: Optional[str] = Field(None, max_length=255)
    role: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None
    account_status: Optional[str] = Field(None, max_length=50)
    driver_id: Optional[int] = None

class UserApprovalAction(BaseModel):
    approved: bool = True
    reason: Optional[str] = Field(None, max_length=255)
    notes: Optional[str] = None
    rejection_reason: Optional[str] = Field(None, max_length=255)

class ApprovalPolicyResponse(BaseModel):
    id: int
    role_name: str
    requires_approval: bool
    allowed_approver_roles: List[str]
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class ApprovalPolicyUpdate(BaseModel):
    requires_approval: bool
    allowed_approver_roles: List[str]

class InvitationValidationResponse(BaseModel):
    valid: bool
    email: Optional[str] = None
    full_name: Optional[str] = None
    role: Optional[str] = None
    message: Optional[str] = None

class AcceptInvitationRequest(BaseModel):
    token: Optional[str] = None
    password: str = Field(..., min_length=6, max_length=128)
    full_name: Optional[str] = Field(None, max_length=255)

class RoleResponse(BaseModel):
    id: Optional[int] = None
    name: str
    description: Optional[str] = None
    permissions: List[str] = []

class PermissionResponse(BaseModel):
    id: Optional[int] = None
    name: str
    resource: str
    action: str
    description: Optional[str] = None
