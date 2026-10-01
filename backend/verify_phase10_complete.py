import sys
import os
import time
import requests
from sqlalchemy import inspect, text

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import engine, SessionLocal
from app.core.config import settings
from app.core.rate_limiter import rate_limiter
from fastapi.testclient import TestClient
from app.main import app

def print_header(title: str):
    print("\n" + "=" * 70)
    print(f" {title.upper()}")
    print("=" * 70)

def print_section(title: str):
    print(f"\n--- {title} ---")

def print_result(label: str, passed: bool, details: str = ""):
    status = " [PASS] " if passed else " [FAIL] "
    detail_str = f" - {details}" if details else ""
    print(f"{status} {label}{detail_str}")

def main():
    print_header("LogiAgent Phase 10: Production Hardening, Security & Performance Verification")
    
    client = TestClient(app)
    total_checks = 0
    passed_checks = 0

    # --------------------------------------------------------------------------
    # 1. SECURITY HEADERS & CORS
    # --------------------------------------------------------------------------
    print_section("1. HTTP Security Headers & CORS Policy")
    res = client.get("/health")
    h = res.headers
    
    c1 = h.get("X-Content-Type-Options") == "nosniff"
    total_checks += 1; passed_checks += int(c1)
    print_result("X-Content-Type-Options: nosniff", c1)

    c2 = h.get("X-Frame-Options") in ["SAMEORIGIN", "DENY"]
    total_checks += 1; passed_checks += int(c2)
    print_result("X-Frame-Options: SAMEORIGIN / DENY", c2)

    c3 = "strict-origin" in h.get("Referrer-Policy", "")
    total_checks += 1; passed_checks += int(c3)
    print_result("Referrer-Policy: strict-origin-when-cross-origin", c3)

    c4 = "Content-Security-Policy" in h
    total_checks += 1; passed_checks += int(c4)
    print_result("Content-Security-Policy header active", c4)

    c5 = len(settings.cors_origins) >= 1
    total_checks += 1; passed_checks += int(c5)
    print_result(f"Configured CORS Origins: {settings.cors_origins}", c5)

    # --------------------------------------------------------------------------
    # 2. REQUEST TRACEABILITY & X-REQUEST-ID
    # --------------------------------------------------------------------------
    print_section("2. Request ID Correlation & Traceability")
    c6 = "X-Request-ID" in h and h["X-Request-ID"].startswith("req-")
    total_checks += 1; passed_checks += int(c6)
    print_result(f"Auto-generated X-Request-ID: {h.get('X-Request-ID')}", c6)

    custom_id = "req-trace-audit-999"
    res_trace = client.get("/health", headers={"X-Request-ID": custom_id})
    c7 = res_trace.headers.get("X-Request-ID") == custom_id
    total_checks += 1; passed_checks += int(c7)
    print_result("Preserved custom client X-Request-ID", c7)

    c8 = "X-Response-Time-Ms" in res.headers
    total_checks += 1; passed_checks += int(c8)
    print_result(f"Response latency tracking header: {h.get('X-Response-Time-Ms')} ms", c8)

    # --------------------------------------------------------------------------
    # 3. STRUCTURED ERROR HANDLING & LEAK PROTECTION
    # --------------------------------------------------------------------------
    print_section("3. Standardized Error Handling & Non-Leakage")
    err_404 = client.get("/api/v1/shipments/SHP-NONEXISTENT-CODE-404")
    data_404 = err_404.json()
    c9 = "error" in data_404 and "code" in data_404["error"] and "request_id" in data_404["error"]
    total_checks += 1; passed_checks += int(c9)
    print_result("Structured error schema on 404/401", c9, f"Code: {data_404.get('error', {}).get('code')}")

    # 422 Validation
    err_422 = client.post("/api/v1/auth/login", json={"email": "invalid"})
    data_422 = err_422.json()
    c10 = err_422.status_code == 422 and data_422["error"]["code"] == "VALIDATION_ERROR"
    total_checks += 1; passed_checks += int(c10)
    print_result("Structured validation error schema on 422", c10, f"Fields: {len(data_422['error']['details'])}")

    # --------------------------------------------------------------------------
    # 4. IN-MEMORY SLIDING WINDOW RATE LIMITING
    # --------------------------------------------------------------------------
    print_section("4. Sliding Window Rate Limiter")
    rate_limiter.reset()
    auth_codes = []
    for _ in range(12):
        r = client.post("/api/v1/auth/login", json={"email": "admin@logiagent.io", "password": "WrongPassword"})
        auth_codes.append(r.status_code)
    
    c11 = 429 in auth_codes
    total_checks += 1; passed_checks += int(c11)
    print_result("Rate limit triggered on rapid auth attempts (HTTP 429)", c11, f"Responses: {auth_codes[:5]}... -> {auth_codes[-2:]}")
    rate_limiter.reset()

    # --------------------------------------------------------------------------
    # 5. INPUT VALIDATION HARDENING
    # --------------------------------------------------------------------------
    print_section("5. Input Validation Hardening (Pydantic Constraints)")
    login_res = client.post("/api/v1/auth/login", json={"email": "admin@logiagent.io", "password": "LogiAgent2026!"})
    token = login_res.json()["access_token"]
    auth_hdr = {"Authorization": f"Bearer {token}"}

    # Shipment negative weight
    v_shp = client.post("/api/v1/shipments", headers=auth_hdr, json={
        "shipment_code": "SHP-INV-WEIGHT",
        "customer_id": 1,
        "origin_id": 1,
        "destination_id": 2,
        "cargo_type": "Standard",
        "weight_kg": -100.0
    })
    c12 = v_shp.status_code == 422
    total_checks += 1; passed_checks += int(c12)
    print_result("Rejected negative cargo weight (weight_kg <= 0)", c12)

    # Driver rating bounds
    v_drv = client.post("/api/v1/drivers", headers=auth_hdr, json={
        "driver_code": "DRV-INV-RATING",
        "name": "Invalid Rating Driver",
        "phone": "+1-555-0199",
        "license_type": "Class A CDL",
        "rating": 6.0
    })
    c13 = v_drv.status_code == 422
    total_checks += 1; passed_checks += int(c13)
    print_result("Enforced driver rating bounds (rating <= 5.0)", c13)

    # Pagination bounds
    v_page = client.get("/api/v1/routes?limit=500", headers=auth_hdr)
    c14 = v_page.status_code == 422
    total_checks += 1; passed_checks += int(c14)
    print_result("Enforced pagination upper bound (limit <= 100)", c14)

    # --------------------------------------------------------------------------
    # 6. DATABASE PERFORMANCE INDEXING
    # --------------------------------------------------------------------------
    print_section("6. Database Indexing & Performance")
    insp = inspect(engine)
    required_indexed_tables = ["shipments", "routes", "vehicles", "drivers", "users", "transportation_costs"]
    idx_count = 0
    for tbl in required_indexed_tables:
        indexes = insp.get_indexes(tbl)
        idx_count += len(indexes)
    
    c15 = idx_count >= 15
    total_checks += 1; passed_checks += int(c15)
    print_result(f"Database performance indexes verified across core models: {idx_count} indexes", c15)

    # --------------------------------------------------------------------------
    # 7. HEALTH PROBES & READINESS
    # --------------------------------------------------------------------------
    print_section("7. Health & Readiness Probes")
    h_base = client.get("/health")
    c16 = h_base.status_code == 200 and h_base.json().get("status") == "healthy"
    total_checks += 1; passed_checks += int(c16)
    print_result("GET /health -> status: healthy", c16)

    h_live = client.get("/health/live")
    c17 = h_live.status_code == 200 and h_live.json().get("status") == "alive"
    total_checks += 1; passed_checks += int(c17)
    print_result("GET /health/live -> status: alive (Liveness Probe)", c17)

    h_ready = client.get("/health/ready")
    c18 = h_ready.status_code == 200 and h_ready.json().get("database") == "connected"
    total_checks += 1; passed_checks += int(c18)
    print_result("GET /health/ready -> database: connected (Readiness Probe)", c18)

    # --------------------------------------------------------------------------
    # 8. RBAC & DATA AUTHORIZATION REGRESSION INTEGRITY
    # --------------------------------------------------------------------------
    print_section("8. RBAC & Security Isolation")
    drv_login = client.post("/api/v1/auth/login", json={"email": "driver@logiagent.io", "password": "LogiAgent2026!"})
    drv_token = drv_login.json()["access_token"]
    
    # Driver blocked from user management
    d_block = client.get("/api/v1/users", headers={"Authorization": f"Bearer {drv_token}"})
    c19 = d_block.status_code == 403
    total_checks += 1; passed_checks += int(c19)
    print_result("RBAC enforcement: Driver blocked from user management (403 Forbidden)", c19)

    # --------------------------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------------------------
    print_header("Phase 10 Verification Summary")
    print(f"Total Verification Checks: {total_checks}")
    print(f"Passed Checks:            {passed_checks}")
    print(f"Failed Checks:            {total_checks - passed_checks}")
    
    if passed_checks == total_checks:
        print("\n>>> ALL PHASE 10 PRODUCTION HARDENING CHECKS PASSED SUCCESSFULLY! <<<\n")
        return 0
    else:
        print("\n>>> SOME PHASE 10 CHECKS FAILED! <<<\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
