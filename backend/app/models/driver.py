from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from datetime import datetime
from app.core.database import Base

class Driver(Base):
    __tablename__ = "drivers"

    id = Column(Integer, primary_key=True, index=True)
    driver_code = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, index=True)
    phone = Column(String(50), nullable=False)
    license_number = Column(String(50), nullable=False)
    license_type = Column(String(50), default="CDL-A", index=True) # CDL-A, CDL-B, Standard
    status = Column(String(50), default="Available", index=True) # Available, Assigned, On Duty, Off Duty, Rest
    rating = Column(Float, default=4.8)
    hours_of_service_remaining = Column(Float, default=11.0) # Maximum 11 hours driving limit under DOT regulations
    current_vehicle_id = Column(Integer, nullable=True, index=True)
    current_latitude = Column(Float, nullable=True)
    current_longitude = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
