from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime
from datetime import datetime
from app.core.database import Base

class ApprovalPolicy(Base):
    __tablename__ = "approval_policies"

    id = Column(Integer, primary_key=True, index=True)
    role_name = Column(String(50), unique=True, index=True, nullable=False) # Driver, Dispatcher, Logistics Manager, Admin
    requires_approval = Column(Boolean, default=True, nullable=False)
    allowed_approver_roles = Column(Text, default="[\"Admin\", \"Logistics Manager\"]") # JSON list of roles
    description = Column(String(255), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
