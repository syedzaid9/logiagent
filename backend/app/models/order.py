from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from datetime import datetime
from app.core.database import Base

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    order_code = Column(String(50), unique=True, index=True, nullable=False) # e.g. ORD-5001
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    order_date = Column(DateTime, default=datetime.utcnow)
    total_value = Column(Float, default=0.0)
    item_count = Column(Integer, default=1)
    status = Column(String(50), default="Confirmed") # Confirmed, Processing, Shipped, Delivered, Cancelled
    created_at = Column(DateTime, default=datetime.utcnow)
