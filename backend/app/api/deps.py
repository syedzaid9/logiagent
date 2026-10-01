from typing import Generator, Optional, List, Union
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.core.security import decode_token
from app.core.permissions import has_permission, get_role_permissions
from app.models.user import User
from app.models.driver import Driver
from app.models.vehicle import Vehicle
from app.schemas.auth import UserResponse

security = HTTPBearer(auto_error=False)

def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def build_user_response(user: User, db: Session) -> UserResponse:
    driver = None
    vehicle = None
    if user.driver_id:
        driver = db.query(Driver).filter(Driver.id == user.driver_id).first()
        if driver and driver.current_vehicle_id:
            vehicle = db.query(Vehicle).filter(Vehicle.id == driver.current_vehicle_id).first()

    permissions = get_role_permissions(user.role)

    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active if user.is_active is not None else True,
        account_status=user.account_status or "Active",
        approval_status=user.approval_status or "Approved",
        driver_id=user.driver_id,
        driver_code=driver.driver_code if driver else None,
        driver_phone=driver.phone if driver else None,
        assigned_vehicle_id=vehicle.id if vehicle else None,
        assigned_vehicle_code=vehicle.vehicle_code if vehicle else None,
        permissions=permissions,
        created_at=user.created_at,
        updated_at=user.updated_at
    )

def get_current_user(
    auth: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    if not auth or not auth.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please provide a valid Bearer token in the Authorization header."
        )
        
    token = auth.credentials
    payload = decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token."
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token subject."
        )

    try:
        u_id = int(user_id)
        user = db.query(User).filter(User.id == u_id).first()
    except (ValueError, TypeError):
        user = db.query(User).filter(User.email == str(user_id)).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Authenticated user account not found in database."
        )

    if not user.is_active or user.account_status == "Deactivated":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated. Access denied."
        )

    if user.account_status == "Suspended":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is currently suspended. Please contact operations administrator."
        )

    if user.approval_status == "Pending_Approval":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is pending authorization from higher authority."
        )

    return user

def require_role(allowed_roles: List[str]):
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        user_role = current_user.role or ""
        if user_role == "Admin":
            return current_user
        
        # Normalize comparison
        normalized_allowed = [r.lower().replace(" ", "") for r in allowed_roles]
        if user_role.lower().replace(" ", "") not in normalized_allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation requires one of the following roles: {allowed_roles}. Current role: '{user_role}'."
            )
        return current_user
    return role_checker

def require_permission(permission: str):
    def permission_checker(current_user: User = Depends(get_current_user)) -> User:
        if not has_permission(current_user.role, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Role '{current_user.role}' lacks permission '{permission}'."
            )
        return current_user
    return permission_checker
