from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.driver import Driver
from app.models.notification import Notification
from app.schemas.notification import NotificationCreate, NotificationResponse
from app.tools.notification_tool import notification_tool

router = APIRouter(prefix="/notifications", tags=["Notification Center"])

@router.get("", response_model=List[NotificationResponse])
def list_notifications(
    status: Optional[str] = Query(None, description="Filter by status (unread, read, sent)"),
    severity: Optional[str] = Query(None, description="Filter by severity (critical, high, medium, low)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Notification)

    # Data scope: Driver only sees their own notifications
    if current_user.role == "Driver":
        driver = db.query(Driver).filter(Driver.id == current_user.driver_id).first() if current_user.driver_id else None
        if not driver:
            return []
        patterns = [driver.name, driver.driver_code, driver.phone or "", driver.email or ""]
        conds = [Notification.recipient.ilike(f"%{p}%") for p in patterns if p]
        conds += [Notification.message.ilike(f"%{p}%") for p in patterns if p]
        if conds:
            query = query.filter(or_(*conds))
        else:
            return []
    if status and status.lower() != "all":
        query = query.filter(Notification.status == status)
    if severity and severity.lower() != "all":
        query = query.filter(Notification.severity == severity)
        
    notifs = query.order_by(Notification.created_at.desc()).all()
    return [NotificationResponse.from_orm(n) for n in notifs]

@router.put("/{notification_id}/read", response_model=NotificationResponse)
def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    notif = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notif:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found.")
    notif.status = "read"
    db.commit()
    db.refresh(notif)
    return NotificationResponse.from_orm(notif)

@router.post("/trigger", response_model=NotificationResponse)
def trigger_notification(
    req: NotificationCreate,
    current_user: User = Depends(get_current_user)
):
    res = notification_tool.execute(**req.dict())
    return NotificationResponse(
        id=res["notification_id"],
        title=res["title"],
        message=req.message,
        notification_type=req.notification_type,
        channel=res["channel"],
        recipient=res["recipient"],
        severity=res["severity"],
        status="sent",
        created_at=res["timestamp"]
    )
