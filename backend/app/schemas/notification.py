from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class NotificationBase(BaseModel):
    title: str
    message: str
    notification_type: str # delay, eta_change, route_deviation, delivery_failure, critical_event
    channel: str = "In-App" # Email, SMS, Push, In-App
    recipient: str
    severity: str = "medium" # low, medium, high, critical
    shipment_id: Optional[int] = None

class NotificationCreate(NotificationBase):
    pass

class NotificationResponse(NotificationBase):
    id: int
    status: str # unread, read, sent, delivered
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
