# LogiAgent — System Architecture Specification

## 1. Overview
LogiAgent is a cloud-native, agentic logistics intelligence platform. It features a LangGraph-orchestrated AI agent sitting between supply chain operators and core systems of record to track shipments, optimize routes, predict delays, analyze costs, and answer complex operational queries in plain natural language.

---

## 2. Architecture Layers

```text
+-------------------------------------------------------------------------------+
| 1. User Layer: Logistics Manager | Dispatcher | Operations Team | Admin       |
+-------------------------------------------------------------------------------+
                                      │
                                      ▼
+-------------------------------------------------------------------------------+
| 2. Frontend Layer: React + TypeScript + Vite + Tailwind CSS + Recharts + Maps  |
+-------------------------------------------------------------------------------+
                                      │
                                HTTPS / REST
                                      │
                                      ▼
+-------------------------------------------------------------------------------+
| 3. API Gateway & FastAPI Backend Services                                      |
|    - Auth & RBAC (/auth)          - Shipments (/shipments)                    |
|    - Vehicles (/vehicles)         - Drivers (/drivers)                        |
|    - Routes (/routes)             - Analytics (/analytics)                    |
|    - ML Predictive (/ml)          - Notifications (/notifications)            |
|    - RAG Knowledge (/rag)         - Agent Assistant (/agent)                  |
+-------------------------------------------------------------------------------+
                                      │
                                      ▼
+-------------------------------------------------------------------------------+
| 4. AI Agent Layer: LogiAgent Core (LangGraph StateGraph)                      |
|    - Intent Understanding -> Tool Selection -> Execution -> Grounded Answer  |
+-------------------------------------------------------------------------------+
                                      │
           ┌──────────────────────────┼──────────────────────────┐
           ▼                          ▼                          ▼
+-----------------------+  +-----------------------+  +-----------------------+
| 5. 9 Agent Tools      |  | 6. RAG Knowledge Base |  | 7. ML & Analytics     |
| - ShipmentTracking    |  | - SOP-LOG-01 (General)|  | - Delay Risk Model    |
| - VehicleAvailability |  | - SOP-LOG-02 (Failed) |  | - ETA Prediction      |
| - DriverManagement    |  | - SOP-LOG-03 (Cold)   |  | - Demand Forecast     |
| - RouteOptimization   |  | - SOP-LOG-04 (HOS)    |  | - Route Efficiency    |
| - ETACalculation      |  | - SOP-LOG-05 (Detent) |  | - Cost Optimizer      |
| - DelayDetection      |  | - SOP-LOG-06 (HAZMAT) |  | - Fleet Utilization   |
| - CostCalculation     |  +-----------------------+  +-----------------------+
| - LogisticsAnalytics  |
| - NotificationTool    |
+-----------------------+
           │
           ▼
+-------------------------------------------------------------------------------+
| 8. Data Layer: Managed PostgreSQL / SQLite + Redis Cache                      |
|    - users, customers, delivery_locations, vehicles, drivers, shipments,     |
|      orders, routes, transportation_costs, shipment_status_history, notifs   |
+-------------------------------------------------------------------------------+
```

---

## 3. The 9 Agent Tools
1. **ShipmentTrackingTool**: Real-time status lookup, coordinates, and delivery history.
2. **VehicleAvailabilityTool**: Capacity matching (weight & volume), vehicle type filtering.
3. **DriverManagementTool**: Hours of Service (HOS) compliance and active assignments.
4. **RouteOptimizationTool**: Best corridor calculation, distance, duration, and toll modeling.
5. **ETACalculationTool**: Dynamic arrival time estimation with traffic slowdown modifiers.
6. **DelayDetectionTool**: Exception detection, bottleneck factor analysis, and risk scoring.
7. **CostCalculationTool**: Fuel burn, labor wages, tolls, and maintenance cost estimation.
8. **LogisticsAnalyticsTool**: Executive KPI summaries, fleet utilization, and on-time SLA metrics.
9. **NotificationTool**: Automated multi-channel alerts (Email, SMS, Push, In-App).

---

## 4. RAG Pipeline
Documents are split into semantic section passages and indexed in the vector store:
- `SOP-LOG-01`: General Logistics Operations, Service Level Agreements & Proof of Delivery
- `SOP-LOG-02`: Failed Delivery and Exception Handling Protocol
- `SOP-LOG-03`: Cold Chain Management & Temperature Compliance
- `SOP-LOG-04`: Driver Hours of Service (HOS) and Safety Regulations
- `SOP-LOG-05`: Detention, Demurrage & Accessorial Surcharges
- `SOP-LOG-06`: Hazardous Materials (HAZMAT) Transport Protocol
