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
    has_token = bool(user.activation_token)
    has_usable_pwd = bool(user.hashed_password and (user.account_status != "Pending_Activation" or not has_token))

    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active if user.is_active is not None else True,
        account_status=user.account_status or "Active",
        approval_status=user.approval_status or "Approved",
        has_usable_password=has_usable_pwd,
        has_activation_token=has_token,
        driver_id=user.driver_id,
        driver_code=driver.driver_code if driver else None,
        driver_name=driver.name if driver else None,
        driver_phone=driver.phone if driver else None,
        assigned_vehicle_id=vehicle.id if vehicle else None,
        assigned_vehicle_code=vehicle.vehicle_code if vehicle else None,
        permissions=permissions,
        created_at=user.created_at,
        updated_at=user.updated_at
    )

def generate_unique_driver_code(db: Session) -> str:
    count = db.query(Driver).count()
    code = f"DRV-{count + 1:02d}"
    idx = count + 1
    while db.query(Driver).filter(Driver.driver_code == code).first():
        idx += 1
        code = f"DRV-{idx:02d}"
    return code

def ensure_driver_profile(
    db: Session,
    user: User,
    name: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    license_number: Optional[str] = None,
    license_type: Optional[str] = "CDL-A"
) -> Driver:
    """
    Finds or creates an operational Driver profile associated with the given user.
    """
    if user.driver_id:
        driver = db.query(Driver).filter(Driver.id == user.driver_id).first()
        if driver:
            return driver

    target_email = email or user.email
    if target_email:
        driver = db.query(Driver).filter(Driver.email == target_email.strip().lower()).first()
        if driver:
            user.driver_id = driver.id
            db.commit()
            db.refresh(user)
            return driver

    # Create new driver profile
    code = generate_unique_driver_code(db)
    drv_name = name or user.full_name or "Commercial Driver"
    drv_email = target_email or f"driver_{code.lower()}@logiagent.com"
    drv_phone = phone or "+1-555-0199"
    drv_lic = license_number or f"DL-{code}-AUTO"

    # Make sure license is unique
    lic_candidate = drv_lic
    lic_idx = 1
    while db.query(Driver).filter(Driver.license_number == lic_candidate).first():
        lic_candidate = f"{drv_lic}-{lic_idx}"
        lic_idx += 1

    new_driver = Driver(
        driver_code=code,
        name=drv_name,
        email=drv_email,
        phone=drv_phone,
        license_number=lic_candidate,
        license_type=license_type or "CDL-A",
        status="Available",
        rating=5.0,
        hours_of_service_remaining=11.0,
        current_latitude=41.9742,
        current_longitude=-87.9073
    )
    db.add(new_driver)
    db.flush()

    user.driver_id = new_driver.id
    db.commit()
    db.refresh(new_driver)
    db.refresh(user)
    return new_driver

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
