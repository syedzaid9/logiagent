# LogiAgent — AI Logistics Operations Agent

> **Production-grade AI logistics operations platform powered by LangGraph, Real Tool Calling, RAG, Predictive ML, and PostgreSQL.**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.111.0-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-1.2-7C3AED?logo=python&logoColor=white)](https://github.com/langchain-ai/langgraph)
[![React](https://img.shields.io/badge/React-18.3-61DAFB?logo=react&logoColor=black)](https://reactjs.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.4-3178C6?logo=typescript&logoColor=white)](https://www.typescriptlang.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?logo=postgresql&logoColor=white)](https://www.postgresql.org)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](https://www.docker.com)

---

## 1. Project Overview
**LogiAgent** is an enterprise AI-driven supply chain operations hub. It positions an autonomous LangGraph agent between logistics operators (Logistics Managers, Dispatchers, Operations Teams) and systems of record. Rather than generating hallucinated responses, LogiAgent dynamically invokes specialized operational tools, accesses real-time telemetry from databases, calculates optimal routes, predicts delay risks using ML models, and grounds compliance queries in company Standard Operating Procedures (SOPs).

---

## 2. Problem Statement
Logistics managers and dispatchers routinely manage dozens of disconnected systems: GPS telematics, TMS platforms, driver hours-of-service logs, weather feeds, and complex regulatory compliance manuals. When exceptions occur (traffic jams, mechanical breakdowns, failed deliveries), determining the right vehicle, calculating detour costs, and verifying company policy requires extensive manual effort.

**LogiAgent solves this by providing a unified conversational and operational cockpit powered by real tool-calling agentic AI.**

---

## 3. Key Features
- 🧠 **LangGraph Orchestrated AI Core**: StateGraph agent executing intent classification, multi-tool chaining, and grounded reasoning.
- 🛠️ **9 Specialized Agent Tools**: Tracking, vehicle availability matching, driver HOS management, route optimization, dynamic ETA prediction, delay risk classification, cost modeling, logistics analytics, and notification dispatches.
- 📦 **Shipment & Fleet Telemetry Management**: 36 pre-seeded shipments, 12 vehicles, and 12 drivers across 15 distribution hubs with live coordinates, delay badges, and status transition audit logs.
- 🗺️ **Interactive Route Visualizer**: Dynamic continental map with turn-by-turn waypoints, traffic condition indicators, polyline corridor rendering, and cost estimators.
- 📜 **RAG Policy Knowledge Base**: Vector-indexed company SOPs covering Failed Deliveries (`SOP-LOG-02`), Cold Chain Compliance (`SOP-LOG-03`), Driver Safety & HOS (`SOP-LOG-04`), Detention & Demurrage (`SOP-LOG-05`), and HAZMAT Regulations (`SOP-LOG-06`).
- 📊 **Predictive ML & Analytics Dashboard**: Feature-based delay risk predictor, time-series 7-day demand volume forecaster, delay root cause analysis, and cost optimization breakdown.
- 🔔 **Event-Driven Notification Center**: Automated multi-channel alerts (In-App, Email, SMS, Push) with priority filters.
- 🔒 **Enterprise RBAC Security**: JWT authentication with persona role-switching for Logistics Managers, Dispatchers, Operations Leads, and Admins.

---

## 4. System Architecture
LogiAgent is built across 10 functional layers based directly on the provided system architecture specification:

```text
Logistics Operators (Manager | Dispatcher | Operations)
                      ↓
          React + TypeScript Frontend
                      ↓
          API Gateway / FastAPI Backend
                      ↓
      LogiAgent LangGraph Reasoning Core
                      ↓
    ┌─────────────────┼─────────────────┐
    ▼                 ▼                 ▼
Agent Tools (9)   RAG Vector Store   ML Predictors
    │                 │                 │
    └─────────────────┼─────────────────┘
                      ▼
         PostgreSQL / SQLite Database
```

---

## 5. Technology Stack
- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS, Recharts, Lucide Icons.
- **Backend**: Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2.0, Uvicorn.
- **AI & Agent Orchestration**: LangGraph, LangChain, Gemini API / OpenAI API integration + deterministic fallback execution engine.
- **Data & Storage**: PostgreSQL 16 (production), SQLite (local zero-setup), Redis 7.
- **DevOps**: Docker, Docker Compose, Nginx.

---

## 6. AI Agent Workflow
When a user submits an operational query:
1. **Intent Understanding**: The `understand_intent` node parses the request, identifies logistics parameters (e.g. `SHP-1001`, `1500 kg`, `delay threshold`), and plans the tool execution chain.
2. **Tool Execution**: The `execute_tools` node dispatches calls to the database and ML modules.
3. **Reasoning & Response Generation**: The `generate_response` node synthesizes grounded results and outputs structured data widgets alongside a transparent **"Actions Performed"** trace.

---

## 7. The 9 Agent Tools

| # | Tool Name | Capabilities |
|---|---|---|
| 1 | `ShipmentTrackingTool` | Real-time status lookup, coordinates, delay duration, and delivery history for any shipment code. |
| 2 | `VehicleAvailabilityTool` | Queries fleet capacity by weight (e.g. 1500 kg), volume, vehicle type, and current location. |
| 3 | `DriverManagementTool` | Queries driver availability, hours-of-service (HOS) remaining, license types, and active assignments. |
| 4 | `RouteOptimizationTool` | Computes fastest/lowest-cost routes, highway corridors, traffic impact, and waypoints. |
| 5 | `ETACalculationTool` | Computes dynamic arrival ETA factoring in transit speed, traffic delays, and mandatory rest stops. |
| 6 | `DelayDetectionTool` | Detects delayed shipments, flags high-risk loads, and provides explainable root-cause factors. |
| 7 | `CostCalculationTool` | Models fuel burn, driver wages, tolls, and maintenance costs per km and fleet-wide. |
| 8 | `LogisticsAnalyticsTool` | Computes on-time delivery rate, fleet capacity utilization, delay distribution, and spend KPIs. |
| 9 | `NotificationTool` | Dispatches automated alerts (Email, SMS, Push, In-App) for delays or exceptions. |

---

## 8. RAG Knowledge Base

LogiAgent includes 6 indexed logistics Standard Operating Procedures:
1. **`SOP-LOG-01`**: General Logistics Operations, Service Level Agreements (SLAs), and Proof of Delivery.
2. **`SOP-LOG-02`**: Failed Delivery & Exception Handling Protocol (15-min driver hold, 24h grace period re-delivery, detention billing).
3. **`SOP-LOG-03`**: Temperature-Controlled Cold Chain Operations (+2°C to +8°C protocols, pre-cooling, excursion procedures).
4. **`SOP-LOG-04`**: Driver Hours of Service (HOS) & DOT Safety Regulations (11h driving limit, 14h duty window, 30m break).
5. **`SOP-LOG-05`**: Detention, Demurrage & Accessorial Charges ($85/hr dry van, $110/hr reefer, 2h free time).
6. **`SOP-LOG-06`**: Hazardous Materials (HAZMAT) Transport Protocol (49 CFR compliance, CDL-A endorsements, tunnel restrictions).

---

## 9. Database Schema
- `users`: User credentials, roles (Admin, Logistics Manager, Dispatcher, Operations Team), timestamps.
- `customers`: Customer codes, enterprise tiers, contact details.
- `delivery_locations`: 15 national logistics distribution centers, warehouses, and customer sites with GPS coordinates.
- `drivers`: License types, CDL numbers, ratings, remaining Hours of Service (HOS), assigned vehicles.
- `vehicles`: Models, vehicle types (Dry Van, Reefer, Flatbed, Box Truck, Sprinter), payload capacity kg, current load, fuel level, GPS position.
- `shipments`: Shipment codes (SHP-1001 to SHP-1036), origin/destination foreign keys, status, weight, ETA, delay minutes, risk scores.
- `routes`: Polyline coordinates, planned vs actual distance/duration, traffic condition, waypoints JSON.
- `transportation_costs`: Distance, fuel cost, labor cost, tolls, maintenance, total cost per trip.
- `shipment_status_history`: Checkpoint audit events with timestamps and locations.
- `notifications`: Alert records, channels (Email, SMS, Push, In-App), severity levels, read states.

---

## 10. API Documentation
When running, FastAPI automatically serves interactive OpenAPI documentation at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

Key endpoints:
- `POST /api/v1/auth/login` — Authenticate and receive JWT token.
- `GET /api/v1/shipments` — Filter, search, and list shipments.
- `GET /api/v1/vehicles` — Query fleet availability and capacity.
- `GET /api/v1/drivers` — Query driver roster and HOS status.
- `GET /api/v1/routes/shipment/{code}` — Compute corridor and waypoints.
- `GET /api/v1/analytics/dashboard` — Executive KPI summary and distributions.
- `POST /api/v1/rag/query` — Semantic vector search across SOP documents.
- `POST /api/v1/agent/chat` — LangGraph agent natural language query interface.

---

## 11. Quick Start & Local Setup

### Prerequisites
- Python 3.11+
- Node.js 18+ & npm
- Docker & Docker Compose (optional for containerized run)

### Option A: One-Click Quick Start (Windows)
Double-click `start_all.bat` (or run `.\start_all.ps1`) from the project root. This automatically starts both the backend API and frontend dev server.

### Option B: Manual Command-Line Setup

1. **Start Backend Server:**
   ```bash
   cd backend
   pip install -r requirements.txt
   py -3.12 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   # Or: python main.py
   ```

2. **Start Frontend Client (in a separate terminal):**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

3. **Access the application:**
   - **Frontend UI**: [http://localhost:5173](http://localhost:5173)
   - **Backend API Docs (Swagger)**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 12. Docker Compose Deployment

Run the complete multi-container stack (Backend, Frontend, PostgreSQL, Redis) with a single command:

```bash
docker compose up --build
```

- **Frontend Application**: `http://localhost:3000`
- **FastAPI Backend & Swagger**: `http://localhost:8000/docs`
- **PostgreSQL Database**: `localhost:5432`

---

## 13. Default Demo Accounts

| Role | Email | Password |
|---|---|---|
| **Logistics Manager** | `manager@logiagent.io` | `manager123` |
| **Dispatcher** | `dispatcher@logiagent.io` | `dispatcher123` |
| **Operations Team** | `ops@logiagent.io` | `ops123` |
| **Admin** | `admin@logiagent.io` | `admin123` |

*(You can also seamlessly toggle personas in real-time from the top navigation bar).*

---

## 14. Verified AI Demo Scenarios

LogiAgent comes with one-click chips in the AI Assistant to test all 7 core scenarios:

### Scenario 1: Shipment Tracking
- **User**: *"Where is shipment SHP-1001?"*
- **Trace**: `Identified intent: Live Shipment Tracking` → `Checked shipment database for SHP-1001` → `Retrieved real-time telemetry for SHP-1001`
- **Output**: Live location on I-80 corridor, origin (Chicago), destination (Dallas), vehicle (TRK-101), driver (Robert McCall), and projected ETA.

### Scenario 2: Exception & Delay Filtering
- **User**: *"Show all delayed shipments."*
- **Trace**: `Identified intent: Filter Delayed Shipments` → `Queried delay detection model & evaluated bottleneck factors` → `Compiled status report`
- **Output**: Structured markdown table with delayed shipments, delay durations, and root causes.

### Scenario 3: Vehicle Availability & Capacity Matching
- **User**: *"Which vehicle is available for a 1500 kg shipment?"*
- **Trace**: `Identified intent: Fleet Vehicle Availability Check` → `Checked vehicle database for available units (1500 kg capacity)` → `Matched 6 suitable vehicles`
- **Output**: Ranked list of vehicles with sufficient available capacity, fuel levels, and current locations.

### Scenario 4: Route Optimization
- **User**: *"Find the fastest route for SHP-1001."*
- **Trace**: `Identified intent: Route Optimization for SHP-1001` → `Calculated optimal highway corridors and traffic conditions`
- **Output**: Interstate corridor recommendation (I-90/I-80), distance (1,496 km), duration (21h 30m), traffic condition, and cost estimation.

### Scenario 5: ML Delay Root-Cause Analysis
- **User**: *"Why is SHP-1001 likely to be delayed?"*
- **Trace**: `Identified intent: Delay Root-Cause Analysis` → `Evaluated delay risk model and generated explainable root-cause factors`
- **Output**: Risk score (68/100, High), analysis of I-80 construction bottlenecks, weather impact, and driver HOS remaining hours.

### Scenario 6: RAG Policy Compliance
- **User**: *"What is the failed delivery policy?"*
- **Trace**: `Analyzed query intent: Logistics Policy & SOP Retrieval` → `Queried Vector Knowledge Base` → `Retrieved grounded policy SOP-LOG-02`
- **Output**: Grounded citation of `SOP-LOG-02` detailing mandatory 15-minute driver wait time, photographic evidence protocol, 24h grace period re-delivery, and storage surcharges.

### Scenario 7: Executive Fleet Performance & Analytics
- **User**: *"How is our fleet performing this month?"*
- **Trace**: `Identified intent: Logistics KPI & Fleet Performance Analysis` → `Aggregated operational KPIs and fleet utilization metrics`
- **Output**: Total active shipments, on-time SLA rate (94.2%), average load utilization (68.5%), and MTD transportation spend ($34,250).

---

## 15. Testing & Quality Assurance

Run the automated test suite covering all tools, authentication, RAG retriever, ML models, and agent scenarios:

```bash
cd backend
python -m pytest tests -v
```

**Results:** `26 passed, 0 failures (100% pass rate)`.

---

## 16. Cloud Deployment Architecture

For production cloud deployment (AWS / GCP / Azure):
- **Compute**: Containerized backend and agent on AWS ECS / GCP Cloud Run / Azure Container Apps.
- **Database**: Managed PostgreSQL (AWS RDS / GCP Cloud SQL / Azure Database for PostgreSQL).
- **Cache**: Managed Redis (AWS ElastiCache / GCP Memorystore).
- **Static Assets**: Frontend CDN on AWS CloudFront + S3 / Cloudflare Pages.
- **Secrets Management**: AWS Secrets Manager / GCP Secret Manager for API keys.

---

## 17. Future Enhancements
- Real-time WebSockets telemetry streaming from physical IoT OBD-II vehicle trackers.
- Autonomous AI agent tool execution for automated dispatcher re-routing.
- Multi-modal invoice and Bill of Lading (BOL) document OCR scanning.

---

## 18. License
Built for Enterprise Logistics Operations under the MIT License.
