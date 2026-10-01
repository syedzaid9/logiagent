from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime

class DocumentChunkResponse(BaseModel):
    id: int
    document_name: str
    document_code: str
    title: str
    category: str
    chunk_index: int
    page_number: Optional[int] = 1
    content: str
    score: Optional[float] = None
    source: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)

class DocumentSummaryResponse(BaseModel):
    id: int
    document_name: str
    document_code: str
    title: str
    category: str
    file_type: str
    total_pages: int
    total_chunks: int
    created_at: Optional[str] = None

class RAGQueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    top_k: int = Field(default=4, ge=1, le=20)
    category: Optional[str] = Field(None, max_length=100)

class RAGQueryResponse(BaseModel):
    query: str
    chunks: List[DocumentChunkResponse]
    answer: Optional[str] = None
    sources_count: int = 0

class DocumentIngestResponse(BaseModel):
    success: bool
    message: str
    document_name: str
    document_code: str
    total_pages: int
    total_chunks: int
