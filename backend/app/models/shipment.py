from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from datetime import datetime
from app.core.database import Base

class Shipment(Base):
    __tablename__ = "shipments"

    id = Column(Integer, primary_key=True, index=True)
    shipment_code = Column(String(50), unique=True, index=True, nullable=False) # e.g. SHP-1001
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    origin_id = Column(Integer, ForeignKey("delivery_locations.id"), nullable=False, index=True)
    destination_id = Column(Integer, ForeignKey("delivery_locations.id"), nullable=False, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=True, index=True)
    driver_id = Column(Integer, ForeignKey("drivers.id"), nullable=True, index=True)
    
    status = Column(String(50), nullable=False, default="Pending", index=True) 
    # Statuses: Pending, Assigned, Picked Up, In Transit, Delayed, Delivered, Failed
    
    cargo_type = Column(String(100), default="General Freight")
    weight_kg = Column(Float, nullable=False, default=1000.0)
    volume_m3 = Column(Float, default=10.0)
    temperature_controlled = Column(Boolean, default=False)
    target_temp_celsius = Column(Float, nullable=True)
    
    current_latitude = Column(Float, nullable=True)
    current_longitude = Column(Float, nullable=True)
    current_location_name = Column(String(255), nullable=True)
    
    pickup_time = Column(DateTime, nullable=True)
    expected_delivery = Column(DateTime, nullable=False, index=True)
    actual_delivery = Column(DateTime, nullable=True)
    estimated_eta = Column(DateTime, nullable=True)
    
    delay_minutes = Column(Integer, default=0)
    delay_reason = Column(String(255), nullable=True)
    delay_risk_score = Column(Float, default=0.0) # 0 to 100
    delay_risk_level = Column(String(50), default="Low") # Low, Medium, High, Critical
    
    special_instructions = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ShipmentStatusHistory(Base):
    __tablename__ = "shipment_status_history"

    id = Column(Integer, primary_key=True, index=True)
    shipment_id = Column(Integer, ForeignKey("shipments.id"), nullable=False, index=True)
    status = Column(String(50), nullable=False, index=True)
    location_name = Column(String(255), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
