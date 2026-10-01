from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from datetime import datetime
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="Driver", index=True)  # Admin, Logistics Manager, Dispatcher, Fleet Manager, Driver, Analyst
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=True, index=True)
    
    # Account & Approval Status
    is_active = Column(Boolean, default=True, index=True)
    account_status = Column(String(50), default="Active", index=True)  # Active, Suspended, Deactivated, Pending_Activation
    approval_status = Column(String(50), default="Approved", index=True)  # Approved, Pending_Approval, Rejected
    
    # Operational Profile Linkage (e.g. Driver)
    driver_id = Column(Integer, ForeignKey("drivers.id"), nullable=True, index=True)
    
    # Invitation & Approvals Audit
    invited_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    activation_token = Column(String(255), nullable=True, index=True)
    activation_expires_at = Column(DateTime, nullable=True)
    auth_user_id = Column(String(255), nullable=True, index=True)  # External Supabase Auth UUID
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
