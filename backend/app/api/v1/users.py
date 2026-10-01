import json
from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user, require_role, require_permission, build_user_response
from app.core.security import get_password_hash, generate_activation_token
from app.core.permissions import (
    PERMISSION_USERS_READ,
    PERMISSION_USERS_MANAGE,
    PERMISSION_USERS_APPROVE,
    PERMISSION_ROLES_MANAGE,
    get_role_permissions,
    get_all_roles,
    get_all_permissions
)
from app.models.user import User
from app.models.role import Role, Permission, RolePermission
from app.models.driver import Driver
from app.models.approval_policy import ApprovalPolicy
from app.schemas.auth import UserResponse
from app.schemas.user import (
    UserProvisionRequest,
    UserProvisionResponse,
    UserUpdateRequest,
    UserApprovalAction,
    ApprovalPolicyResponse,
    ApprovalPolicyUpdate,
    RoleResponse,
    PermissionResponse
)

router = APIRouter(prefix="/users", tags=["User Management & RBAC"])

@router.get("", response_model=List[UserResponse])
def list_users(
    search: Optional[str] = Query(None, description="Search by name or email"),
    role: Optional[str] = Query(None, description="Filter by role"),
    account_status: Optional[str] = Query(None, description="Filter by account status"),
    approval_status: Optional[str] = Query(None, description="Filter by approval status"),
    current_user: User = Depends(require_permission(PERMISSION_USERS_READ)),
    db: Session = Depends(get_db)
):
    """
    List all registered platform users with operational and RBAC profile status.
    """
    query = db.query(User)

    if role and role.lower() != "all":
        query = query.filter(User.role == role)
    if account_status and account_status.lower() != "all":
        query = query.filter(User.account_status == account_status)
    if approval_status and approval_status.lower() != "all":
        query = query.filter(User.approval_status == approval_status)

    users = query.order_by(User.created_at.desc()).all()

    if search and search.strip():
        q = search.strip().lower()
        users = [
            u for u in users
            if q in u.email.lower()
            or q in u.full_name.lower()
            or q in u.role.lower()
        ]

    return [build_user_response(u, db) for u in users]

@router.get("/roles", response_model=List[RoleResponse])
def list_roles(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all database-backed system roles and their assigned permissions.
    """
    db_roles = db.query(Role).all()
    if not db_roles:
        # Fallback to standard definitions
        return [
            RoleResponse(
                id=i + 1,
                name=r["name"],
                description=r["description"],
                permissions=get_role_permissions(r["name"])
            )
            for i, r in enumerate(get_all_roles())
        ]
    
    results = []
    for r in db_roles:
        results.append(RoleResponse(
            id=r.id,
            name=r.name,
            description=r.description,
            permissions=get_role_permissions(r.name)
        ))
    return results

@router.get("/permissions", response_model=List[PermissionResponse])
def list_permissions(
    current_user: User = Depends(require_permission(PERMISSION_USERS_READ)),
    db: Session = Depends(get_db)
):
    """
    List all granular system permissions across logistics domains.
    """
    db_perms = db.query(Permission).all()
    if not db_perms:
        return [
            PermissionResponse(
                id=i + 1,
                name=p["name"],
                resource=p["resource"],
                action=p["action"],
                description=p["description"]
            )
            for i, p in enumerate(get_all_permissions())
        ]
    return [
        PermissionResponse(
            id=p.id,
            name=p.name,
            resource=p.resource,
            action=p.action,
            description=p.description
        )
        for p in db_perms
    ]

@router.post("/provision", response_model=UserProvisionResponse, status_code=status.HTTP_201_CREATED)
def provision_user(
    req: UserProvisionRequest,
    current_user: User = Depends(require_permission(PERMISSION_USERS_MANAGE)),
    db: Session = Depends(get_db)
):
    """
    Provisions a new employee or driver account with cryptographic invitation token.
    """
    email_clean = req.email.strip().lower()
    existing = db.query(User).filter(User.email == email_clean).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User with email '{email_clean}' already exists."
        )

    # Authority hierarchy validation during provisioning
    if current_user.role in ["Logistics Manager", "Fleet Manager"] and req.role in ["Admin", "Logistics Manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Role '{current_user.role}' can only provision Driver or Dispatcher accounts. Role '{req.role}' requires Administrator authority."
        )

    # Validate linked driver if supplied
    driver = None
    if req.driver_id:
        driver = db.query(Driver).filter(Driver.id == req.driver_id).first()
        if not driver:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Driver ID {req.driver_id} not found."
            )

    # Check approval policy
    policy = db.query(ApprovalPolicy).filter(ApprovalPolicy.role_name == req.role).first()
    requires_approval = policy.requires_approval if policy else True
    if req.require_approval is not None:
        requires_approval = req.require_approval

    token = generate_activation_token()
    token_expiry = datetime.utcnow() + timedelta(days=7)

    if (req.auto_approve and current_user.role == "Admin") or not requires_approval:
        approval_st = "Approved"
        account_st = "Pending_Activation"
        approved_by = current_user.id
        approved_at = datetime.utcnow()
    else:
        approval_st = "Pending_Approval"
        account_st = "Pending_Activation"
        approved_by = None
        approved_at = None

    temp_pwd_hash = get_password_hash(generate_activation_token()[:16])

    role_record = db.query(Role).filter(Role.name == req.role).first()

    new_user = User(
        email=email_clean,
        hashed_password=temp_pwd_hash,
        full_name=req.full_name.strip(),
        role=req.role,
        role_id=role_record.id if role_record else None,
        driver_id=req.driver_id,
        is_active=True,
        account_status=account_st,
        approval_status=approval_st,
        invited_by_id=current_user.id,
        approved_by_id=approved_by,
        approved_at=approved_at,
        activation_token=token,
        activation_expires_at=token_expiry
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    msg = f"Account for {email_clean} ({req.role}) provisioned successfully."
    if approval_st == "Pending_Approval":
        msg += " Account is pending higher authority approval before invitation activation."
    else:
        msg += " Invitation activation token generated."

    return UserProvisionResponse(
        success=True,
        message=msg,
        user=build_user_response(new_user, db),
        activation_token=token,
        requires_approval=(approval_st == "Pending_Approval")
    )

@router.post("/{user_id}/approve", response_model=UserResponse)
def approve_user(
    user_id: int,
    action: UserApprovalAction,
    current_user: User = Depends(require_permission(PERMISSION_USERS_APPROVE)),
    db: Session = Depends(get_db)
):
    """
    Authorizes or rejects a pending user account according to approval policy.
    """
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User ID {user_id} not found.")

    # 1. Self-approval protection
    if target.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Users cannot approve their own accounts."
        )

    # 2. Hierarchy of authority check
    policy = db.query(ApprovalPolicy).filter(ApprovalPolicy.role_name == target.role).first()
    allowed_approvers = []
    if policy and policy.allowed_approver_roles:
        try:
            allowed_approvers = json.loads(policy.allowed_approver_roles)
        except Exception:
            allowed_approvers = ["Admin"]
    else:
        allowed_approvers = ["Admin"]

    if current_user.role not in allowed_approvers and current_user.role != "Admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Role '{current_user.role}' lacks authority to approve '{target.role}' accounts. Permitted approvers: {allowed_approvers}"
        )

    if not action.approved:
        target.approval_status = "Rejected"
        target.account_status = "Deactivated"
        target.is_active = False
        target.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(target)
        return build_user_response(target, db)

    # Approved: ensure activation token exists
    if not target.activation_token:
        target.activation_token = generate_activation_token()
    target.activation_expires_at = datetime.utcnow() + timedelta(days=7)

    target.approval_status = "Approved"
    target.account_status = "Pending_Activation" if not target.hashed_password or target.activation_token else "Active"
    target.approved_by_id = current_user.id
    target.approved_at = datetime.utcnow()
    target.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(target)
    return build_user_response(target, db)

@router.post("/{user_id}/suspend", response_model=UserResponse)
def suspend_user(
    user_id: int,
    current_user: User = Depends(require_permission(PERMISSION_USERS_MANAGE)),
    db: Session = Depends(get_db)
):
    """
    Suspends a user account while preserving operational driver & shipment records.
    """
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    if target.id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot suspend your own account.")

    if current_user.role in ["Logistics Manager", "Fleet Manager"] and target.role in ["Admin", "Logistics Manager"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Managers can only suspend Driver or Dispatcher accounts.")

    target.account_status = "Suspended"
    target.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(target)
    return build_user_response(target, db)

@router.post("/{user_id}/activate", response_model=UserResponse)
def activate_user(
    user_id: int,
    current_user: User = Depends(require_permission(PERMISSION_USERS_MANAGE)),
    db: Session = Depends(get_db)
):
    """
    Re-activates a suspended user account.
    """
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    if current_user.role in ["Logistics Manager", "Fleet Manager"] and target.role in ["Admin", "Logistics Manager"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Managers can only manage Driver or Dispatcher accounts.")

    target.account_status = "Active"
    target.is_active = True
    target.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(target)
    return build_user_response(target, db)

@router.get("/policies", response_model=List[ApprovalPolicyResponse])
def get_approval_policies(
    current_user: User = Depends(require_permission(PERMISSION_USERS_READ)),
    db: Session = Depends(get_db)
):
    """
    Lists role approval requirements and authorized approver tiers.
    """
    policies = db.query(ApprovalPolicy).all()
    results = []
    for p in policies:
        approvers = []
        try:
            approvers = json.loads(p.allowed_approver_roles) if p.allowed_approver_roles else ["Admin"]
        except Exception:
            approvers = ["Admin"]
        results.append(ApprovalPolicyResponse(
            id=p.id,
            role_name=p.role_name,
            requires_approval=p.requires_approval,
            allowed_approver_roles=approvers,
            description=p.description
        ))
    return results

@router.put("/policies/{role_name}", response_model=ApprovalPolicyResponse)
def update_approval_policy(
    role_name: str,
    update_data: ApprovalPolicyUpdate,
    current_user: User = Depends(require_role(["Admin"])),
    db: Session = Depends(get_db)
):
    """
    Updates approval governance policy for a specific role (Admin only).
    """
    policy = db.query(ApprovalPolicy).filter(ApprovalPolicy.role_name == role_name).first()
    if not policy:
        policy = ApprovalPolicy(role_name=role_name)
        db.add(policy)

    policy.requires_approval = update_data.requires_approval
    policy.allowed_approver_roles = json.dumps(update_data.allowed_approver_roles)
    policy.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(policy)

    return ApprovalPolicyResponse(
        id=policy.id,
        role_name=policy.role_name,
        requires_approval=policy.requires_approval,
        allowed_approver_roles=update_data.allowed_approver_roles,
        description=policy.description
    )
