import json
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_permission, get_current_user
from app.core.config import settings as app_settings
from app.core.permissions import PERMISSION_SETTINGS_READ, PERMISSION_SETTINGS_MANAGE
from app.models.user import User
from app.models.system_setting import SystemSetting
from app.schemas.system_setting import (
    GeneralSettings,
    ShipmentSettings,
    FleetSettings,
    AIRAGSettings,
    NotificationSettings,
    SecuritySettings,
    SystemSettingsSchema,
    SystemSettingsResponse,
    SystemSettingsUpdateRequest,
    SystemSettingsResetRequest,
)

router = APIRouter(prefix="/settings", tags=["System Settings & Operations Configuration"])

DEFAULT_CATEGORIES = {
    "general": GeneralSettings().model_dump(),
    "shipments": ShipmentSettings().model_dump(),
    "fleet": FleetSettings().model_dump(),
    "ai_rag": AIRAGSettings().model_dump(),
    "notifications": NotificationSettings().model_dump(),
    "security": SecuritySettings().model_dump(),
}

def _get_or_create_settings(db: Session) -> tuple[SystemSettingsSchema, Optional[datetime], Optional[str]]:
    """
    Retrieves all categories from the database, falling back to defaults if not yet created.
    """
    records = db.query(SystemSetting).all()
    records_by_cat = {r.category: r for r in records}
    
    last_updated_at = None
    last_updated_by = None

    merged_data = {}
    for cat_key, default_val in DEFAULT_CATEGORIES.items():
        if cat_key in records_by_cat:
            rec = records_by_cat[cat_key]
            cat_data = default_val.copy()
            cat_data.update(rec.get_config())
            merged_data[cat_key] = cat_data
            if rec.updated_at and (last_updated_at is None or rec.updated_at > last_updated_at):
                last_updated_at = rec.updated_at
                last_updated_by = rec.updated_by
        else:
            merged_data[cat_key] = default_val

    schema = SystemSettingsSchema(
        general=GeneralSettings(**merged_data.get("general", {})),
        shipments=ShipmentSettings(**merged_data.get("shipments", {})),
        fleet=FleetSettings(**merged_data.get("fleet", {})),
        ai_rag=AIRAGSettings(**merged_data.get("ai_rag", {})),
        notifications=NotificationSettings(**merged_data.get("notifications", {})),
        security=SecuritySettings(**merged_data.get("security", {})),
    )
    return schema, last_updated_at, last_updated_by

@router.get("", response_model=SystemSettingsResponse)
def get_system_settings(
    current_user: User = Depends(require_permission(PERMISSION_SETTINGS_READ)),
    db: Session = Depends(get_db)
):
    """
    Retrieve all operational configuration settings across the 6 platform categories.
    Accessible to authorized governance personnel.
    """
    settings_schema, last_updated_at, last_updated_by = _get_or_create_settings(db)
    return SystemSettingsResponse(
        settings=settings_schema,
        last_updated_at=last_updated_at or datetime.utcnow(),
        last_updated_by=last_updated_by or "System Initializer",
        environment=app_settings.ENVIRONMENT,
        version=app_settings.VERSION
    )

@router.put("", response_model=SystemSettingsResponse)
def update_system_settings(
    payload: SystemSettingsUpdateRequest,
    current_user: User = Depends(require_permission(PERMISSION_SETTINGS_MANAGE)),
    db: Session = Depends(get_db)
):
    """
    Update system configuration settings. Strictly restricted to Admin users with `settings:manage` permission.
    Persists modified configuration to the database.
    """
    now = datetime.utcnow()
    updater_email = current_user.email

    if payload.category:
        # Update a single category
        cat_key = payload.category.lower().strip()
        if cat_key not in DEFAULT_CATEGORIES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid category '{payload.category}'. Allowed categories: {list(DEFAULT_CATEGORIES.keys())}"
            )
        
        setting_rec = db.query(SystemSetting).filter(SystemSetting.category == cat_key).first()
        if not setting_rec:
            setting_rec = SystemSetting(category=cat_key)
            db.add(setting_rec)

        current_config = setting_rec.get_config()
        current_config.update(payload.settings)
        setting_rec.set_config(current_config)
        setting_rec.updated_by = updater_email
        setting_rec.updated_at = now
    else:
        # Payload contains multiple categories or full settings dict
        for cat_key, default_val in DEFAULT_CATEGORIES.items():
            if cat_key in payload.settings and isinstance(payload.settings[cat_key], dict):
                setting_rec = db.query(SystemSetting).filter(SystemSetting.category == cat_key).first()
                if not setting_rec:
                    setting_rec = SystemSetting(category=cat_key)
                    db.add(setting_rec)
                
                current_config = setting_rec.get_config()
                current_config.update(payload.settings[cat_key])
                setting_rec.set_config(current_config)
                setting_rec.updated_by = updater_email
                setting_rec.updated_at = now

    db.commit()

    settings_schema, last_updated_at, last_updated_by = _get_or_create_settings(db)
    return SystemSettingsResponse(
        settings=settings_schema,
        last_updated_at=last_updated_at or now,
        last_updated_by=last_updated_by or updater_email,
        environment=app_settings.ENVIRONMENT,
        version=app_settings.VERSION
    )

@router.post("/reset", response_model=SystemSettingsResponse)
def reset_system_settings(
    payload: Optional[SystemSettingsResetRequest] = None,
    current_user: User = Depends(require_permission(PERMISSION_SETTINGS_MANAGE)),
    db: Session = Depends(get_db)
):
    """
    Reset a specific settings category or all categories back to default enterprise parameters.
    """
    now = datetime.utcnow()
    updater_email = current_user.email

    if payload and payload.category:
        cat_key = payload.category.lower().strip()
        if cat_key in DEFAULT_CATEGORIES:
            setting_rec = db.query(SystemSetting).filter(SystemSetting.category == cat_key).first()
            if setting_rec:
                setting_rec.set_config(DEFAULT_CATEGORIES[cat_key])
                setting_rec.updated_by = updater_email
                setting_rec.updated_at = now
    else:
        for cat_key, default_val in DEFAULT_CATEGORIES.items():
            setting_rec = db.query(SystemSetting).filter(SystemSetting.category == cat_key).first()
            if not setting_rec:
                setting_rec = SystemSetting(category=cat_key)
                db.add(setting_rec)
            setting_rec.set_config(default_val)
            setting_rec.updated_by = updater_email
            setting_rec.updated_at = now

    db.commit()

    settings_schema, last_updated_at, last_updated_by = _get_or_create_settings(db)
    return SystemSettingsResponse(
        settings=settings_schema,
        last_updated_at=last_updated_at or now,
        last_updated_by=last_updated_by or updater_email,
        environment=app_settings.ENVIRONMENT,
        version=app_settings.VERSION
    )
