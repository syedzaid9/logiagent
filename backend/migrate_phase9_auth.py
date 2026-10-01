import json
from sqlalchemy import text, inspect
from datetime import datetime
from app.core.database import engine, SessionLocal, Base
from app.core.security import get_password_hash
from app.core.permissions import ALL_SYSTEM_PERMISSIONS, STANDARD_ROLES, ROLE_PERMISSIONS
from app.models.role import Role, Permission, RolePermission
from app.models.approval_policy import ApprovalPolicy
from app.models.user import User
from app.models.driver import Driver
from app.models.vehicle import Vehicle

def run_migration():
    print("Running Phase 9 RBAC & Auth Migration...")
    
    # Create all tables defined in Base metadata
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Check SQLite vs PostgreSQL column inspection for users table
        inspector = inspect(engine)
        existing_cols = [c["name"] for c in inspector.get_columns("users")]
        
        cols_to_add = [
            ("role_id", "INTEGER"),
            ("account_status", "VARCHAR(50) DEFAULT 'Active'"),
            ("approval_status", "VARCHAR(50) DEFAULT 'Approved'"),
            ("driver_id", "INTEGER"),
            ("invited_by_id", "INTEGER"),
            ("approved_by_id", "INTEGER"),
            ("approved_at", "TIMESTAMP"),
            ("activation_token", "VARCHAR(255)"),
            ("activation_expires_at", "TIMESTAMP"),
            ("auth_user_id", "VARCHAR(255)"),
            ("updated_at", "TIMESTAMP")
        ]
        
        for col_name, col_type in cols_to_add:
            if col_name not in existing_cols:
                try:
                    db.execute(text(f"ALTER TABLE users ADD COLUMN {col_name} {col_type};"))
                    db.commit()
                    print(f"Added column: users.{col_name}")
                except Exception as e:
                    db.rollback()
                    print(f"Notice adding users.{col_name}: {e}")

        # 1. Seed Roles
        for r_info in STANDARD_ROLES:
            existing_r = db.query(Role).filter(Role.name == r_info["name"]).first()
            if not existing_r:
                r_obj = Role(name=r_info["name"], description=r_info["description"])
                db.add(r_obj)
        db.commit()

        # 2. Seed Permissions
        for p_info in ALL_SYSTEM_PERMISSIONS:
            existing_p = db.query(Permission).filter(Permission.name == p_info["name"]).first()
            if not existing_p:
                p_obj = Permission(
                    name=p_info["name"],
                    resource=p_info["resource"],
                    action=p_info["action"],
                    description=p_info["description"]
                )
                db.add(p_obj)
        db.commit()

        # 3. Seed Role-Permissions Mapping
        roles_map = {r.name: r for r in db.query(Role).all()}
        perms_map = {p.name: p for p in db.query(Permission).all()}

        for role_name, perm_set in ROLE_PERMISSIONS.items():
            r_obj = roles_map.get(role_name)
            if not r_obj:
                continue
            for perm_name in perm_set:
                p_obj = perms_map.get(perm_name)
                if not p_obj:
                    # Try resource:action
                    continue
                exists = db.query(RolePermission).filter(
                    RolePermission.role_id == r_obj.id,
                    RolePermission.permission_id == p_obj.id
                ).first()
                if not exists:
                    db.add(RolePermission(role_id=r_obj.id, permission_id=p_obj.id))
        db.commit()

        # 4. Seed Approval Policies
        if db.query(ApprovalPolicy).count() == 0:
            policies = [
                ApprovalPolicy(
                    role_name="Driver",
                    requires_approval=True,
                    allowed_approver_roles=json.dumps(["Admin", "Logistics Manager", "Fleet Manager"]),
                    description="Commercial driver accounts require manager or admin approval before activation."
                ),
                ApprovalPolicy(
                    role_name="Dispatcher",
                    requires_approval=True,
                    allowed_approver_roles=json.dumps(["Admin", "Logistics Manager"]),
                    description="Dispatcher accounts require logistics management approval."
                ),
                ApprovalPolicy(
                    role_name="Fleet Manager",
                    requires_approval=True,
                    allowed_approver_roles=json.dumps(["Admin", "Logistics Manager"]),
                    description="Fleet management accounts require director or admin approval."
                ),
                ApprovalPolicy(
                    role_name="Logistics Manager",
                    requires_approval=True,
                    allowed_approver_roles=json.dumps(["Admin"]),
                    description="Management accounts require administrator authorization."
                ),
                ApprovalPolicy(
                    role_name="Analyst",
                    requires_approval=False,
                    allowed_approver_roles=json.dumps(["Admin", "Logistics Manager"]),
                    description="Analyst accounts can be auto-approved or approved by managers."
                ),
                ApprovalPolicy(
                    role_name="Admin",
                    requires_approval=True,
                    allowed_approver_roles=json.dumps(["Admin"]),
                    description="Administrator accounts require primary admin approval."
                )
            ]
            db.add_all(policies)
            db.commit()
            print("Seeded default approval policies.")

        # 5. Seed / Update Core Operational Users
        default_pwd = get_password_hash("LogiAgent2026!")
        
        # Link driver profile if exists
        drv_1 = db.query(Driver).filter(Driver.driver_code == "DRV-01").first()
        drv_5 = db.query(Driver).filter(Driver.driver_code == "DRV-05").first()
        driver_to_link = drv_1 or drv_5 or db.query(Driver).first()
        driver_id_val = driver_to_link.id if driver_to_link else None

        core_users = [
            {
                "email": "admin@logiagent.io",
                "full_name": "Sarah Jenkins (System Admin)",
                "role": "Admin",
                "driver_id": None
            },
            {
                "email": "manager@logiagent.io",
                "full_name": "David Vance (Logistics Director)",
                "role": "Logistics Manager",
                "driver_id": None
            },
            {
                "email": "dispatcher@logiagent.io",
                "full_name": "Marcus Reed (Senior Dispatcher)",
                "role": "Dispatcher",
                "driver_id": None
            },
            {
                "email": "fleet@logiagent.io",
                "full_name": "Carlson Vance (Fleet Manager)",
                "role": "Fleet Manager",
                "driver_id": None
            },
            {
                "email": "driver@logiagent.io",
                "full_name": driver_to_link.name if driver_to_link else "Robert McCall (Commercial Driver)",
                "role": "Driver",
                "driver_id": driver_id_val
            },
            {
                "email": "analyst@logiagent.io",
                "full_name": "Dr. Aris Thorne (Supply Chain Analyst)",
                "role": "Analyst",
                "driver_id": None
            },
            {
                "email": "ops@logiagent.io",
                "full_name": "Elena Rostova (Operations Lead)",
                "role": "Operations Team",
                "driver_id": None
            }
        ]

        for u_info in core_users:
            u_obj = db.query(User).filter(User.email == u_info["email"]).first()
            r_obj = roles_map.get(u_info["role"])
            if not u_obj:
                u_obj = User(
                    email=u_info["email"],
                    hashed_password=default_pwd,
                    full_name=u_info["full_name"],
                    role=u_info["role"],
                    role_id=r_obj.id if r_obj else None,
                    driver_id=u_info["driver_id"],
                    is_active=True,
                    account_status="Active",
                    approval_status="Approved"
                )
                db.add(u_obj)
            else:
                u_obj.hashed_password = default_pwd
                u_obj.full_name = u_info["full_name"]
                u_obj.role = u_info["role"]
                u_obj.role_id = r_obj.id if r_obj else None
                if u_info["driver_id"]:
                    u_obj.driver_id = u_info["driver_id"]
                u_obj.is_active = True
                u_obj.account_status = "Active"
                u_obj.approval_status = "Approved"

        db.commit()
        print("Phase 9 RBAC migration completed successfully!")
    finally:
        db.close()

if __name__ == "__main__":
    run_migration()
