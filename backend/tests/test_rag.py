import pytest
from app.rag import retrieve_relevant_policies, vector_store, initialize_rag
from app.agents.logi_agent import process_agent_query

def test_rag_retrieval_failed_delivery():
    results = retrieve_relevant_policies("What is the company policy for a failed delivery?", top_k=2)
    assert len(results) > 0
    top = results[0]
    assert "SOP-LOG-02" in top["document_code"] or "failed" in top["document_name"].lower()
    assert top["score"] > 0
    assert "page_number" in top

def test_rag_retrieval_vehicle_loading():
    results = retrieve_relevant_policies("What are the vehicle loading requirements and axle weight limits?", top_k=2)
    assert len(results) > 0
    top = results[0]
    assert "SOP-VEH-05" in top["document_code"] or "vehicle" in top["document_name"].lower()
    assert top["score"] > 0

def test_rag_retrieval_driver_safety():
    results = retrieve_relevant_policies("What is the driver safety procedure and emergency triangles placement?", top_k=2)
    assert len(results) > 0
    top = results[0]
    assert "SOP-SAF-08" in top["document_code"] or "driver" in top["document_name"].lower() or "SOP-LOG-04" in top["document_code"]
    assert top["score"] > 0

def test_agent_unknown_question_anti_hallucination():
    res = process_agent_query("What is the company's employee vacation policy?")
    response = res.get("response", "")
    assert "do not contain enough information" in response.lower()

def test_agent_failed_delivery_grounded_response():
    res = process_agent_query("What is the procedure when a customer is unavailable during delivery?")
    response = res.get("response", "")
    sources = res.get("sources", [])
    assert len(sources) > 0
    assert any("SOP-LOG-02" in s.get("document_code", "") or "failed" in s.get("title", "").lower() for s in sources)
    assert any(k in response.lower() for k in ["15 minute", "waiting", "dispatch", "attempt", "den-02"])
