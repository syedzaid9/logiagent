from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from datetime import datetime
from app.core.database import Base

class Route(Base):
    __tablename__ = "routes"

    id = Column(Integer, primary_key=True, index=True)
    route_code = Column(String(50), unique=True, index=True, nullable=False) # e.g. RTE-101
    shipment_id = Column(Integer, ForeignKey("shipments.id"), nullable=True, index=True)
    origin_id = Column(Integer, ForeignKey("delivery_locations.id"), nullable=False, index=True)
    destination_id = Column(Integer, ForeignKey("delivery_locations.id"), nullable=False, index=True)
    
    planned_distance_km = Column(Float, nullable=False)
    actual_distance_km = Column(Float, nullable=True)
    planned_duration_min = Column(Integer, nullable=False)
    actual_duration_min = Column(Integer, nullable=True)
    
    traffic_condition = Column(String(50), default="Moderate") # Light, Moderate, Heavy, Severe Congestion
    weather_condition = Column(String(50), default="Clear") # Clear, Rain, Snow, Fog, Storm
    status = Column(String(50), default="Planned", index=True) # Planned, Assigned, In Transit, Delayed, Completed, Cancelled
    
    waypoints_json = Column(Text, nullable=True) # JSON array of stops
    polyline_json = Column(Text, nullable=True) # JSON array of [lat, lng] coordinates
    estimated_cost = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
