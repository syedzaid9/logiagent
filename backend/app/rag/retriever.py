import os
from typing import List, Dict, Any, Optional
from app.rag.vector_store import vector_store, SupabasePgVectorStore
from app.rag.document_loader import (
    load_documents_from_directory,
    load_single_document,
    DocumentDTO,
    DocumentChunkDTO
)
from app.core.logging_config import logger

def initialize_rag(documents_dirs: Optional[List[str]] = None, force_reindex: bool = False) -> int:
    """
    Initialize Supabase pgvector knowledge base with all documents from documents/ and policies/ directories.
    """
    current_dir = os.path.dirname(os.path.dirname(__file__))
    
    if not documents_dirs:
        documents_dirs = [
            os.path.join(current_dir, "data", "documents"),
            os.path.join(current_dir, "data", "policies"),
        ]

    # Check existing count
    existing_chunks_count = vector_store.count_chunks()
    if existing_chunks_count > 0 and not force_reindex:
        logger.info(f"[Retriever] Supabase pgvector already contains {existing_chunks_count} chunks. Skipping re-indexing.")
        return existing_chunks_count

    all_docs: List[DocumentDTO] = []
    for d in documents_dirs:
        if os.path.exists(d):
            docs = load_documents_from_directory(d)
            all_docs.extend(docs)

    if not all_docs:
        logger.warning("[Retriever] No documents found to index.")
        return 0

    logger.info(f"[Retriever] Ingesting {len(all_docs)} documents into Supabase pgvector store...")
    total_indexed = vector_store.add_documents(all_docs)
    logger.info(f"[Retriever] Ingestion complete: {total_indexed} chunks stored in Supabase.")
    return total_indexed


def ingest_document(file_path: str) -> Optional[Dict[str, Any]]:
    """
    Ingest a single document file into Supabase pgvector.
    """
    doc_dto = load_single_document(file_path)
    if not doc_dto:
        return None

    chunks_added = vector_store.add_documents([doc_dto])
    return {
        "document_name": doc_dto.document_name,
        "document_code": doc_dto.document_code,
        "title": doc_dto.title,
        "category": doc_dto.category,
        "file_type": doc_dto.file_type,
        "total_pages": doc_dto.total_pages,
        "total_chunks": chunks_added
    }


def retrieve_relevant_policies(
    query: str,
    user_role: Optional[str] = None,
    top_k: int = 4,
    category: Optional[str] = None,
    min_similarity: float = 0.05
) -> List[Dict[str, Any]]:
    """
    Retrieve grounded policy and SOP chunks for a user query using Supabase pgvector similarity search,
    strictly enforcing user_role access boundaries BEFORE returning results.
    """
    if vector_store.count_chunks() == 0:
        logger.info("[Retriever] Vector store empty. Auto-initializing RAG documents...")
        initialize_rag()

    results = vector_store.similarity_search(
        query=query,
        user_role=user_role,
        top_k=top_k,
        category=category,
        min_similarity=min_similarity
    )

    formatted = []
    for chunk, score in results:
        formatted.append({
            "document_name": chunk.document_name,
            "document_code": chunk.document_code,
            "title": chunk.title,
            "category": chunk.category,
            "access_scope": chunk.access_scope,
            "chunk_index": chunk.chunk_index,
            "page_number": chunk.page_number or 1,
            "content": chunk.content,
            "score": round(score, 4),
            "metadata": chunk.metadata,
            "source": f"{chunk.document_name} (Page {chunk.page_number or 1})"
        })

    logger.info(f"[Retriever] User Role: [{user_role or 'Anonymous'}] | Query: '{query}' -> Found {len(formatted)} authorized chunks (Top score: {formatted[0]['score'] if formatted else 0.0})")
    return formatted
