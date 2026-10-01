from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Index
from app.core.database import Base

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    alert_code = Column(String(50), unique=True, index=True, nullable=False)
    alert_type = Column(String(50), index=True, nullable=False) # HIGH_DELAY_RISK, ETA_DEADLINE_RISK, ROUTE_ANOMALY, VEHICLE_ISSUE, DRIVER_ISSUE, CAPACITY_ISSUE, COST_ANOMALY
    severity = Column(String(20), index=True, nullable=False, default="MEDIUM") # LOW, MEDIUM, HIGH, CRITICAL
    entity_type = Column(String(50), index=True, nullable=False) # shipment, route, vehicle, driver, system
    entity_id = Column(String(100), index=True, nullable=False) # e.g. SHP-1001, TRK-102, DRV-05
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    evidence = Column(Text, nullable=True) # JSON or structured bullet points
    recommended_action = Column(Text, nullable=True)
    status = Column(String(20), index=True, nullable=False, default="active") # active, acknowledged, resolved
    acknowledged_by = Column(String(100), nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, index=True)

    __table_args__ = (
        Index("ix_alerts_dedup", "alert_type", "entity_type", "entity_id", "status"),
        Index("ix_alerts_created_severity", "created_at", "severity"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "alert_code": self.alert_code,
            "alert_type": self.alert_type,
            "severity": self.severity,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "title": self.title,
            "message": self.message,
            "evidence": self.evidence,
            "recommended_action": self.recommended_action,
            "status": self.status,
            "acknowledged_by": self.acknowledged_by,
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
