import json
import math
from typing import List, Dict, Any, Tuple, Optional
from sqlalchemy import text, inspect
from sqlalchemy.orm import Session
from app.core.database import engine, SessionLocal, Base
from app.core.config import settings
from app.core.logging_config import logger
from app.models.rag_document import Document, DocumentChunk
from app.rag.document_loader import DocumentDTO, DocumentChunkDTO
from app.rag.embeddings import embeddings_service

class SupabasePgVectorStore:
    """
    Production-grade Vector Store using Supabase PostgreSQL + pgvector.
    Stores dense vector embeddings and performs cosine distance similarity searches.
    """

    def __init__(self):
        self._ensure_extension_and_schema()

    def _ensure_extension_and_schema(self):
        """Ensure pgvector extension is enabled and RAG tables exist with correct schema."""
        try:
            with engine.connect() as conn:
                if not settings.DATABASE_URL.startswith("sqlite"):
                    # Enable pgvector extension in PostgreSQL
                    conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
                    conn.commit()
                    logger.info("[SupabasePgVectorStore] pgvector extension verified in PostgreSQL.")
            
            # Inspect existing tables to check if schema migration is needed
            inspector = inspect(engine)
            existing_tables = inspector.get_table_names()

            recreate_rag_tables = False
            if "document_chunks" in existing_tables:
                columns = [c["name"] for c in inspector.get_columns("document_chunks")]
                if "embedding" not in columns or "document_id" not in columns:
                    recreate_rag_tables = True
                    logger.info("[SupabasePgVectorStore] Upgrading legacy document_chunks table schema to pgvector...")

            if recreate_rag_tables:
                DocumentChunk.__table__.drop(bind=engine, checkfirst=True)
                if "documents" in existing_tables:
                    Document.__table__.drop(bind=engine, checkfirst=True)

            Document.__table__.create(bind=engine, checkfirst=True)
            DocumentChunk.__table__.create(bind=engine, checkfirst=True)
            logger.info("[SupabasePgVectorStore] RAG pgvector tables (documents, document_chunks) verified.")

        except Exception as e:
            logger.warning(f"[SupabasePgVectorStore] Schema initialization warning: {e}")


    def add_documents(self, documents: List[DocumentDTO], batch_size: int = 16) -> int:
        """
        Index list of DocumentDTOs with real embeddings into Supabase PostgreSQL.
        Handles duplicates by replacing existing document records.
        """
        if not documents:
            return 0

        db: Session = SessionLocal()
        total_chunks_added = 0

        try:
            for doc in documents:
                # 1. Check & delete existing document with same name for clean upsert
                existing = db.query(Document).filter(Document.document_name == doc.document_name).first()
                if existing:
                    logger.info(f"[SupabasePgVectorStore] Updating existing document '{doc.document_name}'...")
                    db.delete(existing)
                    db.commit()

                # 2. Extract chunk contents for batch embedding
                chunk_texts = [c.content for c in doc.chunks]
                logger.info(f"[SupabasePgVectorStore] Generating embeddings for {len(chunk_texts)} chunks of '{doc.document_name}'...")
                chunk_embeddings = embeddings_service.embed_documents(chunk_texts)

                # 3. Create Document DB record
                roles_json = json.dumps(doc.allowed_roles) if doc.allowed_roles else json.dumps(["Driver", "Dispatcher", "Logistics Manager", "Admin", "Operations Team"])
                db_doc = Document(
                    document_name=doc.document_name,
                    document_code=doc.document_code,
                    title=doc.title,
                    category=doc.category,
                    file_type=doc.file_type,
                    total_pages=doc.total_pages,
                    total_chunks=len(doc.chunks),
                    access_scope=doc.access_scope or "PUBLIC_OPERATIONAL",
                    allowed_roles=roles_json,
                    metadata_json=json.dumps(doc.metadata)
                )
                db.add(db_doc)
                db.flush() # obtain db_doc.id

                # 4. Create DocumentChunk DB records
                db_chunks = []
                for idx, chunk in enumerate(doc.chunks):
                    emb = chunk_embeddings[idx] if idx < len(chunk_embeddings) else None
                    chunk.embedding = emb
                    chunk_roles_json = json.dumps(chunk.allowed_roles) if chunk.allowed_roles else roles_json
                    db_chunk = DocumentChunk(
                        document_id=db_doc.id,
                        document_name=chunk.document_name,
                        document_code=chunk.document_code,
                        title=chunk.title,
                        category=chunk.category,
                        chunk_index=chunk.chunk_index,
                        page_number=chunk.page_number,
                        content=chunk.content,
                        access_scope=chunk.access_scope or doc.access_scope or "PUBLIC_OPERATIONAL",
                        allowed_roles=chunk_roles_json,
                        embedding=emb,
                        metadata_json=json.dumps(chunk.metadata)
                    )
                    db_chunks.append(db_chunk)

                db.add_all(db_chunks)
                db.commit()
                total_chunks_added += len(db_chunks)
                logger.info(f"[SupabasePgVectorStore] Successfully indexed '{doc.document_name}' ({doc.access_scope}) with {len(db_chunks)} chunks.")

            return total_chunks_added

        except Exception as e:
            db.rollback()
            logger.error(f"[SupabasePgVectorStore] Error indexing documents: {e}", exc_info=True)
            raise e
        finally:
            db.close()

    def similarity_search(
        self,
        query: str,
        user_role: Optional[str] = None,
        top_k: int = 4,
        category: Optional[str] = None,
        min_similarity: float = 0.05
    ) -> List[Tuple[DocumentChunkDTO, float]]:
        """
        Execute vector similarity search in Supabase PostgreSQL using pgvector cosine distance (<=>).
        Strictly applies user_role security filtering BEFORE vector search results are returned.
        """
        clean_query = query.strip()
        if not clean_query:
            return []

        # 1. Generate query vector
        query_vector = embeddings_service.embed_text(clean_query)
        vec_str = "[" + ",".join(str(float(x)) for x in query_vector) + "]"

        is_postgres = not settings.DATABASE_URL.startswith("sqlite")
        is_admin = bool(user_role and user_role.upper().replace(" ", "_") == "ADMIN")
        role_clean = user_role.replace("_", " ").title() if user_role else ""
        role_norm = user_role.upper().replace(" ", "_") if user_role else ""

        if is_postgres:
            # Native PostgreSQL pgvector cosine similarity search with server-side role filtering
            sql = """
            SELECT 
                dc.id,
                dc.document_name,
                dc.document_code,
                dc.title,
                dc.category,
                dc.chunk_index,
                dc.page_number,
                dc.content,
                dc.access_scope,
                dc.allowed_roles,
                dc.metadata_json,
                (1.0 - (dc.embedding <=> CAST(:query_vec AS vector))) AS similarity_score
            FROM document_chunks dc
            WHERE (CAST(:category_filter AS VARCHAR) IS NULL OR dc.category ILIKE CAST(:category_filter AS VARCHAR))
              AND (
                CAST(:is_admin AS BOOLEAN) = TRUE
                OR dc.access_scope = 'PUBLIC_OPERATIONAL'
                OR dc.allowed_roles ILIKE CAST(:role_filter AS VARCHAR)
                OR dc.allowed_roles ILIKE CAST(:role_filter_alt AS VARCHAR)
              )
            ORDER BY dc.embedding <=> CAST(:query_vec AS vector) ASC
            LIMIT :top_k;
            """

            try:
                with engine.connect() as conn:
                    result = conn.execute(
                        text(sql),
                        {
                            "query_vec": vec_str,
                            "category_filter": f"%{category}%" if category else None,
                            "is_admin": is_admin,
                            "role_filter": f"%\"{role_clean}\"%" if role_clean else "%",
                            "role_filter_alt": f"%\"{role_norm}\"%" if role_norm else "%",
                            "top_k": top_k
                        }
                    ).fetchall()

                    matched_results: List[Tuple[DocumentChunkDTO, float]] = []
                    for row in result:
                        score = float(row.similarity_score) if row.similarity_score is not None else 0.0
                        
                        # Apply minimum similarity threshold
                        if score < min_similarity:
                            continue

                        meta = json.loads(row.metadata_json) if row.metadata_json else {}
                        roles = json.loads(row.allowed_roles) if row.allowed_roles else []
                        chunk_dto = DocumentChunkDTO(
                            document_name=row.document_name,
                            document_code=row.document_code,
                            title=row.title,
                            category=row.category,
                            chunk_index=row.chunk_index,
                            page_number=row.page_number,
                            content=row.content,
                            access_scope=row.access_scope or "PUBLIC_OPERATIONAL",
                            allowed_roles=roles,
                            metadata=meta
                        )
                        matched_results.append((chunk_dto, round(score, 4)))

                    return matched_results
            except Exception as e:
                logger.error(f"[SupabasePgVectorStore] pgvector similarity search failed: {e}", exc_info=True)

        # Fallback / SQLite vector similarity calculation with strict role pre-filtering
        db: Session = SessionLocal()
        try:
            chunks = db.query(DocumentChunk).all()
            scored: List[Tuple[DocumentChunk, float]] = []
            
            for c in chunks:
                if category and category.lower() not in c.category.lower():
                    continue

                # Pre-filter by user role BEFORE vector score evaluation
                if user_role:
                    chunk_roles = []
                    if c.allowed_roles:
                        try:
                            chunk_roles = json.loads(c.allowed_roles)
                        except Exception:
                            chunk_roles = []
                    
                    is_public = (c.access_scope == "PUBLIC_OPERATIONAL")
                    norm_chunk_roles = [r.upper().replace(" ", "_") for r in chunk_roles]
                    if not is_public and not is_admin and role_norm not in norm_chunk_roles and user_role not in chunk_roles:
                        continue

                if c.embedding:
                    # Cosine similarity
                    c_emb = c.embedding
                    dot = sum(a * b for a, b in zip(query_vector, c_emb))
                    norm_a = math.sqrt(sum(a * a for a in query_vector))
                    norm_b = math.sqrt(sum(b * b for b in c_emb))
                    sim = dot / (norm_a * norm_b) if norm_a > 0 and norm_b > 0 else 0.0
                    if sim >= min_similarity:
                        scored.append((c, sim))

            scored.sort(key=lambda x: x[1], reverse=True)
            results = []
            for c, score in scored[:top_k]:
                meta = json.loads(c.metadata_json) if c.metadata_json else {}
                roles = json.loads(c.allowed_roles) if c.allowed_roles else []
                chunk_dto = DocumentChunkDTO(
                    document_name=c.document_name,
                    document_code=c.document_code,
                    title=c.title,
                    category=c.category,
                    chunk_index=c.chunk_index,
                    page_number=c.page_number,
                    content=c.content,
                    access_scope=c.access_scope or "PUBLIC_OPERATIONAL",
                    allowed_roles=roles,
                    metadata=meta
                )
                results.append((chunk_dto, round(score, 4)))
            return results
        finally:
            db.close()

    def list_documents(self, user_role: Optional[str] = None) -> List[Dict[str, Any]]:
        """Return list of indexed documents accessible to the given role."""
        db: Session = SessionLocal()
        is_admin = bool(user_role and user_role.upper().replace(" ", "_") == "ADMIN")
        role_norm = user_role.upper().replace(" ", "_") if user_role else ""
        try:
            docs = db.query(Document).order_by(Document.id).all()
            filtered_docs = []
            for d in docs:
                allowed_roles = []
                if d.allowed_roles:
                    try:
                        allowed_roles = json.loads(d.allowed_roles)
                    except Exception:
                        allowed_roles = []
                
                if user_role and not is_admin:
                    norm_doc_roles = [r.upper().replace(" ", "_") for r in allowed_roles]
                    if d.access_scope != "PUBLIC_OPERATIONAL" and role_norm not in norm_doc_roles and user_role not in allowed_roles:
                        continue

                filtered_docs.append({
                    "id": d.id,
                    "document_name": d.document_name,
                    "document_code": d.document_code,
                    "title": d.title,
                    "category": d.category,
                    "file_type": d.file_type,
                    "access_scope": d.access_scope,
                    "allowed_roles": allowed_roles,
                    "total_pages": d.total_pages,
                    "total_chunks": d.total_chunks,
                    "created_at": d.created_at.isoformat() if d.created_at else None
                })
            return filtered_docs
        finally:
            db.close()

    def count_chunks(self) -> int:
        """Return total number of chunks stored in Supabase pgvector."""
        db: Session = SessionLocal()
        try:
            return db.query(DocumentChunk).count()
        finally:
            db.close()

vector_store = SupabasePgVectorStore()
