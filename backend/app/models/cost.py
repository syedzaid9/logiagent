from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from datetime import datetime
from app.core.database import Base

class TransportationCost(Base):
    __tablename__ = "transportation_costs"

    id = Column(Integer, primary_key=True, index=True)
    shipment_id = Column(Integer, ForeignKey("shipments.id"), nullable=False, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=True, index=True)
    
    distance_km = Column(Float, nullable=False, default=100.0)
    fuel_cost = Column(Float, nullable=False, default=0.0)
    driver_wage_cost = Column(Float, nullable=False, default=0.0)
    toll_cost = Column(Float, default=0.0)
    maintenance_cost = Column(Float, default=0.0)
    accessorial_cost = Column(Float, default=0.0)
    total_cost = Column(Float, nullable=False, default=0.0)
    cost_per_km = Column(Float, default=0.0)
    currency = Column(String(10), default="USD")
    calculated_at = Column(DateTime, default=datetime.utcnow, index=True)
