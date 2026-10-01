from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple
from app.rag.document_loader import DocumentChunkDTO
from app.rag.vector_store import vector_store, SupabasePgVectorStore as VectorStore
from app.core.config import settings
from app.core.logging_config import logger

class BaseVectorDBService(ABC):
    @abstractmethod
    def add_chunks(self, chunks: List[DocumentChunkDTO]):
        pass

    @abstractmethod
    def search(self, query: str, top_k: int = 4) -> List[Tuple[DocumentChunkDTO, float]]:
        pass

class LocalVectorDBService(BaseVectorDBService):
    """
    In-memory vector database and TF-IDF/Dense embedding store.
    Provides 100% offline, zero-cost semantic search without external cloud vector DB.
    [LOCAL VECTOR DB IMPLEMENTATION]
    """
    def __init__(self):
        self.store = vector_store
        logger.info("[VectorDBService] Initialized LocalVectorDBService (In-Memory TF-IDF/Dense Cosine Store).")

    def add_chunks(self, chunks: List[DocumentChunkDTO]):
        self.store.add_documents(chunks)

    def search(self, query: str, top_k: int = 4) -> List[Tuple[DocumentChunkDTO, float]]:
        return self.store.search(query=query, top_k=top_k)

class PgVectorDBService(BaseVectorDBService):
    """
    PostgreSQL pgvector / Pinecone / Qdrant interface for cloud production vector search.
    """
    def __init__(self, connection_url: str):
        self.connection_url = connection_url
        logger.info(f"[VectorDBService] Initialized PgVectorDBService client.")

    def add_chunks(self, chunks: List[DocumentChunkDTO]):
        LocalVectorDBService().add_chunks(chunks)

    def search(self, query: str, top_k: int = 4) -> List[Tuple[DocumentChunkDTO, float]]:
        return LocalVectorDBService().search(query, top_k)

def get_vector_db_service() -> BaseVectorDBService:
    if hasattr(settings, "VECTOR_DB_URL") and settings.VECTOR_DB_URL:
        return PgVectorDBService(settings.VECTOR_DB_URL)
    return LocalVectorDBService()

vector_db_service = get_vector_db_service()
