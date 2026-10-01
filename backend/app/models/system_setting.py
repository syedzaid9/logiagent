from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
import json
from app.core.database import Base

class SystemSetting(Base):
    __tablename__ = "system_settings"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(String(50), unique=True, index=True, nullable=False) # general, shipments, fleet, ai_rag, notifications, security
    config_json = Column(Text, nullable=False, default="{}") # JSON encoded payload
    updated_by = Column(String(100), nullable=True) # Email of the user who modified it
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def get_config(self) -> dict:
        try:
            return json.loads(self.config_json) if self.config_json else {}
        except Exception:
            return {}

    def set_config(self, data: dict):
        self.config_json = json.dumps(data)
