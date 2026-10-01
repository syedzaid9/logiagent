from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from datetime import datetime
from app.core.database import Base

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(String(50), nullable=False) # delay, eta_change, route_deviation, delivery_failure, critical_event
    channel = Column(String(50), default="In-App") # Email, SMS, Push, In-App
    recipient = Column(String(255), nullable=False)
    status = Column(String(50), default="unread") # unread, read, sent, delivered
    severity = Column(String(50), default="medium") # low, medium, high, critical
    shipment_id = Column(Integer, ForeignKey("shipments.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
