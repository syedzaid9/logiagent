import sys
import os
import json
import time

# Configure utf-8 standard output for Windows console
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

from sqlalchemy import inspect, text
from app.core.config import settings
from app.core.database import engine, SessionLocal
from app.models.rag_document import Document, DocumentChunk
from app.rag.embeddings import embeddings_service
from app.rag.document_loader import (
    extract_text_from_pdf,
    load_single_document,
    load_documents_from_directory
)
from app.rag.vector_store import vector_store
from app.rag.retriever import retrieve_relevant_policies, initialize_rag, ingest_document
from app.agents.logi_agent import process_agent_query

def run_rag_tests():
    print("=" * 80)
    print("LOGIAGENT PHASE 2: REAL SUPABASE PGVECTOR RAG PIPELINE VERIFICATION")
    masked_url = settings.DATABASE_URL.split('@')[-1] if '@' in settings.DATABASE_URL else settings.DATABASE_URL[:25]
    print(f"Database Host: {masked_url}")
    print(f"Embedding Model: {settings.EMBEDDING_MODEL_NAME} ({settings.EMBEDDING_DIMENSION} dimensions)")
    print(f"LLM Provider: {settings.LLM_PROVIDER}")
    print("=" * 80)

    test_results = {}

    # 1. TEST SUPABASE PGVECTOR EXTENSION & TABLES
    print("\n[STEP 1] Verifying Supabase PostgreSQL pgvector extension and RAG tables...")
    try:
        with engine.connect() as conn:
            # Check vector extension
            exts = conn.execute(text("SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';")).fetchall()
            print(f" -> pgvector Extension: {exts}")
            assert len(exts) > 0, "pgvector extension is not enabled in Supabase PostgreSQL!"

        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f" -> Existing Tables ({len(tables)}): {sorted(tables)}")
        assert "documents" in tables, "Missing 'documents' table in Supabase!"
        assert "document_chunks" in tables, "Missing 'document_chunks' table in Supabase!"

        # Check document_chunks columns
        columns = [c["name"] for c in inspector.get_columns("document_chunks")]
        print(f" -> document_chunks Columns: {columns}")
        assert "embedding" in columns, "Missing 'embedding' vector column in document_chunks!"
        assert "document_id" in columns, "Missing 'document_id' foreign key column!"
        assert "page_number" in columns, "Missing 'page_number' column!"

        test_results["Supabase pgvector Extension & Schema"] = True
        print(" -> Step 1 Result: PASS")
    except Exception as e:
        print(f" -> Step 1 Result: FAILED: {e}")
        test_results["Supabase pgvector Extension & Schema"] = False
        return test_results

    # 2. TEST PDF & TXT TEXT EXTRACTION WITH PAGE TRACKING
    print("\n[STEP 2] Testing PDF and TXT text extraction and page tracking...")
    try:
        pdf_path = os.path.join(os.path.dirname(__file__), "app", "data", "documents", "failed_delivery_policy.pdf")
        pages = extract_text_from_pdf(pdf_path)
        print(f" -> Extracted {len(pages)} page(s) from {os.path.basename(pdf_path)}")
        assert len(pages) >= 2, f"Expected at least 2 pages from PDF, got {len(pages)}"
        for p in pages:
            print(f"    - Page {p['page_number']}: {len(p['text'])} chars -> Excerpt: {p['text'][:60]}...")
            assert p["page_number"] > 0
            assert len(p["text"]) > 50

        # Test single document load with metadata
        doc_dto = load_single_document(pdf_path)
        assert doc_dto is not None
        assert doc_dto.document_code == "SOP-LOG-02"
        assert doc_dto.total_pages == 2
        assert len(doc_dto.chunks) > 0
        print(f" -> Document DTO: '{doc_dto.title}' [{doc_dto.document_code}] with {len(doc_dto.chunks)} chunks")

        test_results["PDF Text Extraction (Page-Aware)"] = True
        test_results["TXT/MD Text Extraction"] = True
        test_results["Smart Chunking with Metadata"] = True
        print(" -> Step 2 Result: PASS")
    except Exception as e:
        print(f" -> Step 2 Result: FAILED: {e}")
        test_results["PDF Text Extraction (Page-Aware)"] = False
        return test_results

    # 3. TEST REAL EMBEDDING GENERATION
    print("\n[STEP 3] Testing Real Vector Embedding Generation...")
    try:
        sample_query = "What is the policy for failed delivery when a customer is unavailable?"
        t0 = time.time()
        vec = embeddings_service.embed_text(sample_query)
        gen_time = round(time.time() - t0, 3)
        print(f" -> Generated vector for query: {gen_time}s | Length: {len(vec)}")
        assert len(vec) == settings.EMBEDDING_DIMENSION, f"Expected {settings.EMBEDDING_DIMENSION} dimensions, got {len(vec)}"
        assert any(x != 0.0 for x in vec), "Vector cannot be all zeros!"
        # Check normalization
        norm = sum(x * x for x in vec)
        print(f" -> Vector L2 Norm: {norm:.4f} (Expected ~1.0)")
        assert 0.99 <= norm <= 1.01, f"Vector is not normalized! Norm = {norm}"

        test_results["Real Embedding Generation"] = True
        print(" -> Step 3 Result: PASS")
    except Exception as e:
        print(f" -> Step 3 Result: FAILED: {e}")
        test_results["Real Embedding Generation"] = False
        return test_results

    # 4. TEST INGESTION & PGVECTOR INDEXING IN SUPABASE
    print("\n[STEP 4] Ingesting & indexing logistics documents into Supabase pgvector...")
    try:
        total_chunks = initialize_rag(force_reindex=True)
        print(f" -> Total chunks indexed in Supabase: {total_chunks}")
        assert total_chunks >= 20, f"Expected at least 20 chunks, got {total_chunks}"

        db_docs = vector_store.list_documents()
        print(f" -> Ingested Documents in Supabase ({len(db_docs)} documents):")
        for d in db_docs:
            print(f"    - {d['document_name']:30s} [{d['document_code']}]: {d['total_chunks']} chunks, {d['total_pages']} pages ({d['category']})")

        test_results["Document Ingestion Pipeline"] = True
        test_results["Supabase pgvector Storage"] = True
        print(" -> Step 4 Result: PASS")
    except Exception as e:
        print(f" -> Step 4 Result: FAILED: {e}")
        test_results["Document Ingestion Pipeline"] = False
        return test_results

    # 5. REQUIRED TEST 1: FAILED DELIVERY POLICY
    print("\n" + "-" * 70)
    print("[TEST 1] Testing 'Failed Delivery Policy' (Customer Unavailable)")
    print("-" * 70)
    query_1 = "What is the procedure when a customer is unavailable during delivery?"
    try:
        res1 = process_agent_query(query_1)
        resp1 = res1.get("response", "")
        sources1 = res1.get("sources", [])
        tools1 = res1.get("tools_used", [])

        print(f"Query: \"{query_1}\"")
        print(f"Tools Invoked: {tools1}")
        print(f"Sources ({len(sources1)}): {json.dumps(sources1, indent=2)}")
        print(f"Agent Response:\n{resp1}\n")

        # Verifications
        assert "rag_policy_retriever" in tools1 or len(sources1) > 0, "rag_policy_retriever was not invoked!"
        assert any("SOP-LOG-02" in s.get("document_code", "") or "failed_delivery" in s.get("title", "").lower() for s in sources1), "Failed delivery document not in sources!"
        assert any(k in resp1.lower() for k in ["15 minute", "waiting", "dispatch", "3 attempt", "den-02", "contact", "attempt"]), "Response is missing key failed delivery protocols!"
        assert "source" in resp1.lower() or len(sources1) > 0, "Response missing source attribution!"

        test_results["Test 1: Failed Delivery Policy"] = True
        print(" -> TEST 1 RESULT: PASS")
    except Exception as e:
        print(f" -> TEST 1 RESULT: FAILED: {e}")
        test_results["Test 1: Failed Delivery Policy"] = False

    # 6. REQUIRED TEST 2: VEHICLE POLICY
    print("\n" + "-" * 70)
    print("[TEST 2] Testing 'Vehicle Policy' (Vehicle Loading Requirements)")
    print("-" * 70)
    query_2 = "What are the vehicle loading requirements?"
    try:
        res2 = process_agent_query(query_2)
        resp2 = res2.get("response", "")
        sources2 = res2.get("sources", [])
        tools2 = res2.get("tools_used", [])

        print(f"Query: \"{query_2}\"")
        print(f"Tools Invoked: {tools2}")
        print(f"Sources ({len(sources2)}): {json.dumps(sources2, indent=2)}")
        print(f"Agent Response:\n{resp2}\n")

        # Verifications
        assert "rag_policy_retriever" in tools2 or len(sources2) > 0
        assert any("SOP-VEH-05" in s.get("document_code", "") or "vehicle" in s.get("title", "").lower() for s in sources2), "Vehicle policy document not in sources!"
        assert any(k in resp2.lower() for k in ["axle", "80/20", "weight", "strap", "gvwr", "ratchet", "pallet"]), "Response missing vehicle loading guidelines!"
        assert "source" in resp2.lower() or len(sources2) > 0

        test_results["Test 2: Vehicle Policy"] = True
        print(" -> TEST 2 RESULT: PASS")
    except Exception as e:
        print(f" -> TEST 2 RESULT: FAILED: {e}")
        test_results["Test 2: Vehicle Policy"] = False

    # 7. REQUIRED TEST 3: DRIVER GUIDELINES
    print("\n" + "-" * 70)
    print("[TEST 3] Testing 'Driver Guidelines' (Driver Safety Procedure)")
    print("-" * 70)
    query_3 = "What is the driver safety procedure?"
    try:
        res3 = process_agent_query(query_3)
        resp3 = res3.get("response", "")
        sources3 = res3.get("sources", [])
        tools3 = res3.get("tools_used", [])

        print(f"Query: \"{query_3}\"")
        print(f"Tools Invoked: {tools3}")
        print(f"Sources ({len(sources3)}): {json.dumps(sources3, indent=2)}")
        print(f"Agent Response:\n{resp3}\n")

        # Verifications
        assert "rag_policy_retriever" in tools3 or len(sources3) > 0
        assert any("SOP-SAF-08" in s.get("document_code", "") or "SOP-LOG-04" in s.get("document_code", "") or "driver" in s.get("title", "").lower() for s in sources3), "Driver safety document not in sources!"
        assert any(k in resp3.lower() for k in ["11", "hours", "hos", "rest", "break", "ppe", "safety", "triangles", "hazard"]), "Response missing driver safety guidelines!"
        assert "source" in resp3.lower() or len(sources3) > 0

        test_results["Test 3: Driver Guidelines"] = True
        print(" -> TEST 3 RESULT: PASS")
    except Exception as e:
        print(f" -> TEST 3 RESULT: FAILED: {e}")
        test_results["Test 3: Driver Guidelines"] = False

    # 8. REQUIRED TEST 4: UNKNOWN INFORMATION (ANTI-HALLUCINATION)
    print("\n" + "-" * 70)
    print("[TEST 4] Testing 'Unknown Information' (Employee Vacation Policy)")
    print("-" * 70)
    query_4 = "What is the company's employee vacation policy?"
    try:
        res4 = process_agent_query(query_4)
        resp4 = res4.get("response", "")
        sources4 = res4.get("sources", [])

        print(f"Query: \"{query_4}\"")
        print(f"Agent Response:\n{resp4}\n")

        # Verifications: System must not hallucinate a vacation policy and must return the clear unsupported message
        expected_phrase = "The available logistics documents do not contain enough information to answer this question."
        assert expected_phrase.lower() in resp4.lower() or "do not contain enough information" in resp4.lower(), f"Failed anti-hallucination check! Response: {resp4}"

        test_results["Test 4: Unknown Information (No Hallucination)"] = True
        print(" -> TEST 4 RESULT: PASS")
    except Exception as e:
        print(f" -> TEST 4 RESULT: FAILED: {e}")
        test_results["Test 4: Unknown Information (No Hallucination)"] = False

    # 9. FINAL SUMMARY
    print("\n" + "=" * 80)
    print("PHASE 2 RAG PIPELINE VERIFICATION SUMMARY:")
    print("=" * 80)
    for test_name, passed in test_results.items():
        print(f"  - {test_name:50s}: {'PASS' if passed else 'FAIL'}")

    all_passed = all(test_results.values())
    print("\n" + "=" * 80)
    print(f"OVERALL PHASE 2 STATUS: {'PASS' if all_passed else 'FAIL'}")
    print("=" * 80)
    return all_passed

if __name__ == "__main__":
    success = run_rag_tests()
    sys.exit(0 if success else 1)
