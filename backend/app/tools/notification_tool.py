from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from app.tools.base import BaseAgentTool
from app.core.database import SessionLocal
from app.models.notification import Notification
from app.models.shipment import Shipment
from app.core.logging_config import logger

class NotificationTool(BaseAgentTool):
    name: str = "notification_tool"
    description: str = (
        "Trigger operator alerts, automated customer emails, SMS notifications, and push dispatches "
        "for shipment delays, critical ETA changes, route deviations, or delivery failures."
    )
    allowed_roles: List[str] = ["ADMIN", "LOGISTICS_MANAGER", "DISPATCHER", "DRIVER"]
    required_permissions: List[str] = ["notifications:send"]
    data_scope: str = "Role-scoped notification dispatch"

    def execute(
        self,
        title: str,
        message: str,
        notification_type: str = "delay", # delay, eta_change, route_deviation, delivery_failure, critical_event
        channel: str = "In-App", # Email, SMS, Push, In-App
        recipient: str = "ops-team@logiagent.io",
        severity: str = "medium", # low, medium, high, critical
        shipment_code: Optional[str] = None,
        user_context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        
        ctx = user_context or getattr(self, "user_context", None) or {}
        user_role = (ctx.get("role") or "").upper().replace(" ", "_")
        driver_id = ctx.get("driver_id")

        db: Session = SessionLocal()
        try:
            shipment_id = None
            if shipment_code:
                code_clean = shipment_code.strip().upper()
                s = db.query(Shipment).filter(Shipment.shipment_code == code_clean).first()
                if not s:
                    s = db.query(Shipment).filter(Shipment.shipment_code.like(f"%{code_clean}%")).first()

                if s:
                    # Parameter authorization for driver
                    if user_role == "DRIVER" and driver_id:
                        if s.driver_id and s.driver_id != driver_id:
                            return {
                                "success": False,
                                "error": "Unauthorized: You can only link notifications to your own assigned shipments."
                            }
                    shipment_id = s.id


            notif = Notification(
                title=title,
                message=message,
                notification_type=notification_type,
                channel=channel,
                recipient=recipient,
                severity=severity,
                shipment_id=shipment_id,
                status="sent"
            )
            db.add(notif)
            db.commit()
            db.refresh(notif)

            logger.info(f"Notification triggered [{notification_type.upper()}] to {recipient} via {channel}: {title}")

            return {
                "success": True,
                "notification_id": notif.id,
                "title": notif.title,
                "channel": notif.channel,
                "recipient": notif.recipient,
                "severity": notif.severity,
                "status": "Delivered successfully",
                "timestamp": notif.created_at.isoformat()
            }

        finally:
            db.close()

notification_tool = NotificationTool()
