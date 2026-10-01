from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from datetime import datetime
from app.core.database import Base

class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_code = Column(String(50), unique=True, index=True, nullable=False) # e.g. TRK-101
    model = Column(String(100), nullable=False)
    type = Column(String(50), nullable=False, index=True) # Semi-Truck (Dry Van), Reefer (Refrigerated), Flatbed, Box Truck, Sprinter Van
    max_capacity_kg = Column(Float, nullable=False)
    current_load_kg = Column(Float, default=0.0)
    max_volume_m3 = Column(Float, default=80.0)
    current_volume_m3 = Column(Float, default=0.0)
    status = Column(String(50), default="Available", index=True) # Available, Assigned, In Transit, Maintenance
    current_location = Column(String(255), default="Central Distribution Hub")
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    fuel_level_pct = Column(Float, default=100.0)
    fuel_type = Column(String(50), default="Diesel") # Diesel, Electric, Hybrid
    mileage_km = Column(Float, default=45000.0)
    driver_id = Column(Integer, nullable=True, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
