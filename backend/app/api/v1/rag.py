import os
import shutil
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, UploadFile, File, HTTPException
from app.api.deps import get_current_user, require_role
from app.models.user import User
from app.rag import retrieve_relevant_policies, vector_store, ingest_document, initialize_rag
from app.schemas.rag import (
    RAGQueryRequest,
    RAGQueryResponse,
    DocumentChunkResponse,
    DocumentSummaryResponse,
    DocumentIngestResponse
)
from app.core.logging_config import logger

router = APIRouter(prefix="/rag", tags=["RAG Policy & SOP Knowledge Base"])

@router.post("/query", response_model=RAGQueryResponse)
def query_policies(
    req: RAGQueryRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Execute real vector similarity search against Supabase PostgreSQL using pgvector,
    strictly enforcing role-based document scoping.
    """
    results = retrieve_relevant_policies(query=req.query, user_role=current_user.role, top_k=req.top_k, category=req.category)
    chunks = [
        DocumentChunkResponse(
            id=i + 1,
            document_name=r.get("document_name", "document.pdf"),
            document_code=r.get("document_code", "SOP"),
            title=r.get("title", "Logistics Policy"),
            category=r.get("category", "Operations"),
            chunk_index=r.get("chunk_index", i),
            page_number=r.get("page_number", 1),
            content=r.get("content", ""),
            score=r.get("score"),
            source=r.get("source"),
            metadata=r.get("metadata")
        ) for i, r in enumerate(results)
    ]
    return RAGQueryResponse(
        query=req.query,
        chunks=chunks,
        answer=f"Retrieved {len(chunks)} grounded policy sections from Supabase pgvector.",
        sources_count=len(chunks)
    )

@router.get("/documents", response_model=List[DocumentSummaryResponse])
def list_indexed_documents(
    current_user: User = Depends(get_current_user)
):
    """
    List all indexed logistics documents accessible to the current user's role.
    """
    docs = vector_store.list_documents(user_role=current_user.role)
    return [
        DocumentSummaryResponse(
            id=d["id"],
            document_name=d["document_name"],
            document_code=d["document_code"],
            title=d["title"],
            category=d["category"],
            file_type=d["file_type"],
            total_pages=d["total_pages"],
            total_chunks=d["total_chunks"],
            created_at=d.get("created_at")
        )
        for d in docs
    ]

@router.post("/upload", response_model=DocumentIngestResponse)
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(require_role(["Admin", "Logistics Manager"]))
):
    """
    Upload and ingest a new logistics document (PDF, TXT, MD) into Supabase pgvector.
    """
    filename = file.filename
    ext = os.path.splitext(filename)[1].lower()
    if ext not in [".pdf", ".txt", ".md"]:
        raise HTTPException(status_code=400, detail=f"Unsupported file format '{ext}'. Only .pdf, .txt, .md supported.")

    upload_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "documents"))
    os.makedirs(upload_dir, exist_ok=True)
    target_path = os.path.join(upload_dir, filename)

    with open(target_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    res = ingest_document(target_path)
    if not res:
        raise HTTPException(status_code=500, detail="Failed to parse and extract text from uploaded document.")

    return DocumentIngestResponse(
        success=True,
        message=f"Document '{filename}' successfully processed and indexed into Supabase pgvector.",
        document_name=res["document_name"],
        document_code=res["document_code"],
        total_pages=res["total_pages"],
        total_chunks=res["total_chunks"]
    )

@router.post("/reindex")
def reindex_all_documents(
    current_user: User = Depends(require_role(["Admin", "Logistics Manager"]))
):
    """
    Re-scan documents/ and policies/ directories and re-index all documents into Supabase pgvector.
    """
    total = initialize_rag(force_reindex=True)
    return {
        "success": True,
        "message": f"Successfully re-indexed {total} chunks into Supabase pgvector.",
        "total_chunks": total
    }
