from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
from app.core.database import Base

class DeliveryLocation(Base):
    __tablename__ = "delivery_locations"

    id = Column(Integer, primary_key=True, index=True)
    location_code = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    address = Column(String(255), nullable=False)
    city = Column(String(100), nullable=False)
    state = Column(String(50), nullable=False)
    postal_code = Column(String(20), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    hub_type = Column(String(50), default="Distribution Center") # Warehouse, Distribution Center, Fulfillment Hub, Customer Site
    created_at = Column(DateTime, default=datetime.utcnow)
