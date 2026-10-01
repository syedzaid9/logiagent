from datetime import datetime
from typing import List, Optional
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.types import UserDefinedType
from app.core.database import Base
from app.core.config import settings

class PgVector(UserDefinedType):
    """
    PostgreSQL pgvector column type with seamless Python list conversion.
    Falls back gracefully if used on SQLite.
    """
    def __init__(self, dim: int = 384):
        self.dim = dim

    def get_col_spec(self, **kw):
        return f"vector({self.dim})"

    def bind_processor(self, dialect):
        def process(value):
            if value is None:
                return None
            if isinstance(value, (list, tuple)):
                return "[" + ",".join(str(float(x)) for x in value) + "]"
            return str(value)
        return process

    def result_processor(self, dialect, coltype):
        def process(value):
            if value is None:
                return None
            if isinstance(value, str):
                val_str = value.strip("[]() ")
                if not val_str:
                    return []
                return [float(x.strip()) for x in val_str.split(",") if x.strip()]
            return list(value)
        return process


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    document_name = Column(String(255), unique=True, index=True, nullable=False) # e.g. failed_delivery_policy.pdf
    document_code = Column(String(100), index=True, nullable=False) # e.g. SOP-LOG-02
    title = Column(String(255), nullable=False)
    category = Column(String(100), index=True, nullable=False) # e.g. Exception Management
    file_type = Column(String(20), nullable=False, default="pdf") # pdf, txt, md
    total_pages = Column(Integer, default=1)
    total_chunks = Column(Integer, default=0)
    access_scope = Column(String(100), default="PUBLIC_OPERATIONAL", index=True) # PUBLIC_OPERATIONAL, DRIVER, DISPATCHER, MANAGER, ADMIN, RESTRICTED
    allowed_roles = Column(Text, nullable=True) # JSON list e.g. '["Driver", "Dispatcher", "Logistics Manager", "Admin"]'
    metadata_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=True, index=True)
    document_name = Column(String(255), index=True, nullable=False) # e.g. failed_delivery_policy.pdf
    document_code = Column(String(100), index=True, nullable=False) # e.g. SOP-LOG-02
    title = Column(String(255), nullable=False)
    category = Column(String(100), index=True, nullable=False) # Policy, Safety, Compliance, Operations
    chunk_index = Column(Integer, nullable=False)
    page_number = Column(Integer, nullable=True) # Page 1, 2, 3...
    content = Column(Text, nullable=False)
    access_scope = Column(String(100), default="PUBLIC_OPERATIONAL", index=True)
    allowed_roles = Column(Text, nullable=True) # JSON list of roles allowed to view chunk
    embedding = Column(PgVector(settings.EMBEDDING_DIMENSION), nullable=True)
    metadata_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    document = relationship("Document", back_populates="chunks")
