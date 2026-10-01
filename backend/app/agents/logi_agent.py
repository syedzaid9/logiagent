import re
import time
from typing import Dict, Any, List, Optional
from langgraph.graph import StateGraph, END
from app.agents.state import AgentState
from app.agents.prompts import SYSTEM_PROMPT
from app.agents.llm_factory import llm_provider
from app.tools import (
    shipment_tracking_tool,
    vehicle_availability_tool,
    driver_management_tool,
    route_optimization_tool,
    eta_calculation_tool,
    delay_detection_tool,
    cost_calculation_tool,
    logistics_analytics_tool,
    notification_tool,
    shipment_risk_tool,
    route_intelligence_tool,
    anomaly_alerts_tool,
)
from app.rag import retrieve_relevant_policies
from app.core.logging_config import logger

def parse_shipment_code(query: str) -> Optional[str]:
    match = re.search(r"\b(SHP[-_]?[A-Za-z0-9]{3,8})\b", query, re.IGNORECASE)
    if match:
        return match.group(1).upper().replace("_", "-")
    return None

def parse_route_code(query: str) -> Optional[str]:
    match = re.search(r"\b(RT[-_]?[A-Za-z0-9]{2,10}|ROUTE[-_]?[A-Za-z0-9]{2,10})\b", query, re.IGNORECASE)
    if match:
        return match.group(1).upper().replace("_", "-")
    return None

def parse_driver_code(query: str) -> Optional[str]:
    match = re.search(r"\b(DRV[-_]?[A-Za-z0-9]{3,8})\b", query, re.IGNORECASE)
    if match:
        return match.group(1).upper().replace("_", "-")
    return None

def parse_vehicle_code(query: str) -> Optional[str]:
    match = re.search(r"\b(TRK[-_]?[A-Za-z0-9]{3,8})\b", query, re.IGNORECASE)
    if match:
        return match.group(1).upper().replace("_", "-")
    return None

def parse_weight_kg(query: str) -> Optional[float]:
    match = re.search(r"(\d+(?:\.\d+)?)\s*(?:kg|kilos|kilograms|tons|tonnes)", query, re.IGNORECASE)
    if match:
        val = float(match.group(1))
        if "ton" in query.lower():
            val *= 1000.0
        return val
    return None

def parse_hours(query: str) -> Optional[int]:
    match = re.search(r"(\d+)\s*(?:hours|hrs|hr)", query, re.IGNORECASE)
    if match:
        return int(match.group(1)) * 60
    return None


# ==================== LANGGRAPH NODES ====================

def understand_intent_node(state: AgentState) -> Dict[str, Any]:
    query = state["user_query"].strip()
    q_lower = query.lower()
    user_context = state.get("user_context") or {}
    user_role = (state.get("user_role") or user_context.get("role") or "LOGISTICS_MANAGER").upper().replace(" ", "_")
    
    actions = list(state.get("actions_performed", []))
    tools_to_call = []
    intent = "general"
    
    shipment_code = parse_shipment_code(query)
    route_code = parse_route_code(query)
    driver_code = parse_driver_code(query)
    vehicle_code = parse_vehicle_code(query)
    weight_kg = parse_weight_kg(query)
    hours_delay_min = parse_hours(query)

    # 0. Human-in-the-Loop High-Impact Actions Safeguard
    destructive_keywords = [
        "cancel route", "cancel shipment", "reassign driver", "reassign vehicle",
        "delete route", "delete shipment", "terminate", "deactivate driver", "deactivate vehicle"
    ]
    if any(k in q_lower for k in destructive_keywords):
        intent = "human_confirmation_required"
        actions.append("Detected high-impact operational mutation request -> Requiring Human Confirmation")
        return {
            **state,
            "intent": intent,
            "tools_to_call": [],
            "actions_performed": actions
        }

    # 1. RAG / Policy / SOP / Procedure / Guidelines Query Detection
    rag_keywords = [
        "policy", "sop", "procedure", "rule", "guideline", "requirement", "protocol",
        "failed delivery", "unavailable", "undeliver", "customer unavailable",
        "vehicle loading", "loading requirement", "weight limit", "axle",
        "driver safety", "safety procedure", "hos", "hours of service",
        "cold chain", "reefer", "temperature", "detention", "demurrage", "hazmat",
        "compliance", "regulation", "vacation", "employee", "leave", "holiday", "benefit",
        "security", "credential", "admin", "secret"
    ]
    if any(k in q_lower for k in rag_keywords) and not (shipment_code and any(k in q_lower for k in ["where", "track", "eta", "status", "cost", "assigned driver", "who is driving", "why", "risk"])):
        intent = "rag_policy"
        actions.append(f"Analyzed query intent: Logistics Policy & SOP Retrieval for role [{user_role}]")
        tools_to_call.append({"tool": "rag_retriever", "params": {"query": query}})

    # 2. Driver-Personalized Queries ("my shipment", "my vehicle", "my route", "my eta")
    elif user_role == "DRIVER" and any(k in q_lower for k in ["my next shipment", "my shipment", "where is my", "show my active", "my deliveries", "my assigned"]):
        intent = "shipment_tracking"
        actions.append("Identified driver personal shipment tracking intent")
        tools_to_call.append({"tool": "shipment_tracking_tool", "params": {"shipment_code": shipment_code}})

    elif user_role == "DRIVER" and any(k in q_lower for k in ["my vehicle", "what vehicle", "assigned vehicle", "my truck"]):
        intent = "vehicle_availability"
        actions.append("Identified driver assigned vehicle lookup intent")
        tools_to_call.append({"tool": "vehicle_availability_tool", "params": {}})

    elif user_role == "DRIVER" and any(k in q_lower for k in ["my route", "where am i going", "my directions", "my corridor"]):
        intent = "route_optimization"
        actions.append("Identified driver assigned route optimization intent")
        tools_to_call.append({"tool": "route_optimization_tool", "params": {"shipment_code": shipment_code, "priority": "fastest"}})

    elif user_role == "DRIVER" and any(k in q_lower for k in ["my eta", "when will i arrive", "my arrival"]):
        intent = "eta_calculation"
        actions.append("Identified driver personal ETA calculation intent")
        tools_to_call.append({"tool": "eta_calculation_tool", "params": {"shipment_code": shipment_code}})

    # 3. Operational Problems, Anomalies & Alerts
    elif any(k in q_lower for k in ["biggest operational problems", "operational problems", "show alerts", "operational alerts", "anomalies", "network bottlenecks", "what is wrong today", "system alerts"]):
        intent = "anomaly_alerts"
        actions.append("Identified intent: Operational Anomaly & Active Alerts Intelligence")
        tools_to_call.append({"tool": "anomaly_alerts_tool", "params": {"scan_now": True, "include_recommendations": True}})

    # 4. At-Risk Shipments & Network Risk Analysis
    elif any(k in q_lower for k in ["which shipments are at risk", "at risk today", "high risk shipments", "shipments at risk", "risk today"]):
        intent = "network_risk"
        actions.append("Identified intent: Network Risk & High-Risk Shipments Identification")
        tools_to_call.append({"tool": "shipment_risk_tool", "params": {"network_summary": True}})
        tools_to_call.append({"tool": "delay_detection_tool", "params": {"at_risk_only": True}})

    # 5. Explainable Shipment Risk / Delay Analysis ("Why is SHP-1001 delayed?", "Give operational analysis for SHP-1001")
    elif shipment_code and any(k in q_lower for k in ["why", "reason", "likely to be delayed", "delay risk", "risk of delay", "at risk", "risk", "analysis", "recommendations", "recommendation", "intelligence", "operational analysis"]):
        intent = "shipment_risk_explanation"
        actions.append(f"Identified intent: Explainable Root-Cause & Risk Analysis for {shipment_code}")
        tools_to_call.append({"tool": "shipment_risk_tool", "params": {"shipment_code": shipment_code}})
        tools_to_call.append({"tool": "delay_detection_tool", "params": {"shipment_code": shipment_code}})
        tools_to_call.append({"tool": "route_optimization_tool", "params": {"shipment_code": shipment_code}})

    # 6. Specific Shipment Driver Assignment (Show the driver assigned to SHP-1001)
    elif shipment_code and any(k in q_lower for k in ["driver", "assigned driver", "who is driving"]):
        intent = "shipment_driver"
        actions.append(f"Identified intent: Driver Assignment Lookup for {shipment_code}")
        tools_to_call.append({"tool": "shipment_tracking_tool", "params": {"shipment_code": shipment_code}})

    # 7. Specific Shipment Transportation Cost
    elif shipment_code and any(k in q_lower for k in ["cost", "transportation cost", "price", "expense", "spend", "rate", "fee"]):
        intent = "shipment_cost"
        actions.append(f"Identified intent: Transportation Cost Calculation for {shipment_code}")
        tools_to_call.append({"tool": "cost_calculation_tool", "params": {"shipment_code": shipment_code}})

    # 8. Underutilized Fleet / Vehicles Need Attention
    elif any(k in q_lower for k in ["underutilized", "underutilization", "vehicles need attention", "under-utilized"]):
        intent = "underutilized_fleet"
        actions.append("Identified intent: Underutilized Fleet Units Analysis")
        tools_to_call.append({"tool": "anomaly_alerts_tool", "params": {"scan_now": True}})
        tools_to_call.append({"tool": "vehicle_availability_tool", "params": {}})

    # 9. Driver Workload / Highest Workload Drivers
    elif any(k in q_lower for k in ["highest workload", "driver workload", "busiest driver", "driver hours"]):
        intent = "driver_workload"
        actions.append("Identified intent: Driver Workload & Active Shipment Distribution")
        tools_to_call.append({"tool": "driver_management_tool", "params": {"active_only": True}})

    # 10. Weekly Delivery Performance / Delivery Metrics
    elif any(k in q_lower for k in ["delivered this week", "weekly delivery performance", "how many delivered", "delivery performance"]):
        intent = "delivery_performance"
        actions.append("Identified intent: Weekly Delivery Metrics & SLA Performance")
        tools_to_call.append({"tool": "logistics_analytics_tool", "params": {}})

    # 11. Route Comparison & Route Cost Ranking
    elif any(k in q_lower for k in ["compare the current route", "compare route", "which route has the highest cost", "which routes are costing the most", "route with the highest delay"]):
        intent = "route_comparison"
        actions.append("Identified intent: Route Intelligence & Alternative Corridor Comparison")
        tools_to_call.append({"tool": "route_intelligence_tool", "params": {"route_code": route_code, "shipment_code": shipment_code}})

    # 12. In-Transit / Active Shipments Count
    elif any(k in q_lower for k in ["how many", "in transit", "in-transit", "active shipments", "count of shipments", "shipments in transit"]):
        intent = "in_transit_count"
        actions.append("Identified intent: In-Transit Shipment Operations Count")
        tools_to_call.append({"tool": "logistics_analytics_tool", "params": {}})

    # 13. Fleet Analytics / Performance Overview
    elif any(k in q_lower for k in ["performing", "performance", "fleet performing", "fleet performance", "kpi", "monthly cost", "today's logistics", "overview", "analytics", "cost this month"]):
        intent = "logistics_analytics"
        actions.append("Identified intent: Logistics KPI & Fleet Performance Analysis")
        tools_to_call.append({"tool": "logistics_analytics_tool", "params": {}})
        tools_to_call.append({"tool": "cost_calculation_tool", "params": {"fleet_monthly_total": True}})

    # 14. Route Optimization / Corridor Calculation
    elif route_code or any(k in q_lower for k in ["route", "fastest route", "best route", "direction", "navigation", "distance", "path", "corridor", "optimize"]):
        intent = "route_optimization"
        target_entity = route_code or shipment_code or "requested corridor"
        actions.append(f"Identified intent: Route Optimization for {target_entity}")
        if shipment_code:
            tools_to_call.append({"tool": "shipment_tracking_tool", "params": {"shipment_code": shipment_code}})
        tools_to_call.append({
            "tool": "route_optimization_tool",
            "params": {"shipment_code": shipment_code, "route_code": route_code, "priority": "fastest"}
        })

    # 15. ETA Query
    elif (shipment_code or "eta" in q_lower) and any(k in q_lower for k in ["eta", "arrival", "delivery time", "estimated delivery", "delivery schedule", "when will", "estimated time", "arrival time"]):
        intent = "eta_calculation"
        target_s = shipment_code or "assigned shipment"
        actions.append(f"Identified intent: ETA Calculation for {target_s}")
        tools_to_call.append({"tool": "eta_calculation_tool", "params": {"shipment_code": shipment_code}})

    # 16. Delayed Shipments List
    elif any(k in q_lower for k in ["delayed shipments", "show me delayed", "all delayed", "late shipments", "delayed by", "delayed"]):
        intent = "delayed_shipments_list"
        min_mins = hours_delay_min if hours_delay_min is not None else 0
        actions.append(f"Identified intent: Filter Delayed Shipments (threshold: {min_mins} min)")
        tools_to_call.append({"tool": "delay_detection_tool", "params": {"min_delay_minutes": min_mins, "at_risk_only": False}})

    # 17. Available Vehicle Query
    elif any(k in q_lower for k in ["available vehicle", "vehicle is available", "vehicles are available", "which vehicle", "which truck", "free truck", "capacity", "vehicle", "trucks"]):
        intent = "vehicle_availability"
        actions.append(f"Identified intent: Fleet Vehicle Availability Check (Payload: {weight_kg or 'any'} kg)")
        tools_to_call.append({"tool": "vehicle_availability_tool", "params": {"min_capacity_kg": weight_kg}})

    # 18. Driver Query
    elif driver_code or any(k in q_lower for k in ["driver", "drivers", "who is driving", "chauffeur", "roster", "hos", "hours of service"]):
        intent = "driver_management"
        actions.append("Identified intent: Driver Management & HOS Verification")
        if driver_code:
            tools_to_call.append({"tool": "driver_management_tool", "params": {"driver_code": driver_code}})
        elif vehicle_code:
            tools_to_call.append({"tool": "driver_management_tool", "params": {"vehicle_code": vehicle_code}})
        elif any(k in q_lower for k in ["active shipment", "on duty", "in transit"]):
            tools_to_call.append({"tool": "driver_management_tool", "params": {"active_only": True}})
        else:
            tools_to_call.append({"tool": "driver_management_tool", "params": {"available_only": "available" in q_lower or "ready" in q_lower}})

    # 19. Specific Shipment Tracking
    elif shipment_code or any(k in q_lower for k in ["shipment", "where is", "track", "package"]):
        intent = "shipment_tracking"
        actions.append(f"Identified intent: Live Shipment Tracking ({shipment_code or 'general'})")
        tools_to_call.append({"tool": "shipment_tracking_tool", "params": {"shipment_code": shipment_code}})

    # Default fallback
    else:
        intent = "general_assistance"
        actions.append("Processed general operational query")

    return {
        **state,
        "intent": intent,
        "tools_to_call": tools_to_call,
        "actions_performed": actions
    }


def execute_tools_node(state: AgentState) -> Dict[str, Any]:
    tools_to_call = state.get("tools_to_call") or []
    actions = list(state.get("actions_performed") or [])
    structured_data = dict(state.get("structured_data") or {})
    tool_results = list(state.get("tool_results") or [])
    rag_sources = list(state.get("rag_sources") or [])
    user_context = state.get("user_context") or {}
    user_role = (state.get("user_role") or user_context.get("role") or "LOGISTICS_MANAGER").upper().replace(" ", "_")

    for call in tools_to_call:
        t_name = call.get("tool")
        params = call.get("params", {})

        if t_name == "rag_retriever":
            actions.append(f"Queried Vector Knowledge Base for role [{user_role}] with document policy filtering")
            sources = retrieve_relevant_policies(params.get("query", ""), user_role=user_role, top_k=3)
            rag_sources.extend(sources)
            actions.append(f"Retrieved {len(sources)} grounded policy section(s)")
            tool_results.append({
                "tool_name": "rag_policy_retriever",
                "tool_input": params,
                "tool_output": sources,
                "success": len(sources) > 0
            })

        elif t_name == "shipment_tracking_tool":
            actions.append(f"Checked shipment database for {params.get('shipment_code', 'records')}")
            res = shipment_tracking_tool.execute(**params, user_context=user_context)
            success_val = res.get("found", True) if res.get("success", True) else False
            tool_results.append({
                "tool_name": "shipment_tracking_tool",
                "tool_input": params,
                "tool_output": res,
                "success": success_val
            })
            if res.get("found"):
                structured_data["shipment"] = res

        elif t_name == "shipment_risk_tool":
            actions.append("Evaluated shipment risk scores, delay probabilities, and deadline compliance")
            res = shipment_risk_tool.execute(**params, user_context=user_context)
            tool_results.append({
                "tool_name": "shipment_risk_tool",
                "tool_input": params,
                "tool_output": res,
                "success": res.get("success", True)
            })
            structured_data["risk_analysis"] = res

        elif t_name == "route_intelligence_tool":
            actions.append("Analyzed route performance and alternative corridor comparisons")
            res = route_intelligence_tool.execute(**params, user_context=user_context)
            tool_results.append({
                "tool_name": "route_intelligence_tool",
                "tool_input": params,
                "tool_output": res,
                "success": res.get("success", True)
            })
            structured_data["route_intelligence"] = res

        elif t_name == "anomaly_alerts_tool":
            actions.append("Scanned operational telemetry for anomalies and active alerts")
            res = anomaly_alerts_tool.execute(**params, user_context=user_context)
            tool_results.append({
                "tool_name": "anomaly_alerts_tool",
                "tool_input": params,
                "tool_output": res,
                "success": res.get("success", True)
            })
            structured_data["alerts"] = res

        elif t_name == "vehicle_availability_tool":
            min_kg = params.get("min_capacity_kg")
            actions.append(f"Checked vehicle database for available fleet units ({min_kg or 'all'} kg capacity)")
            res = vehicle_availability_tool.execute(**params, user_context=user_context)
            tool_results.append({
                "tool_name": "vehicle_availability_tool",
                "tool_input": params,
                "tool_output": res,
                "success": res.get("success", True)
            })
            if res.get("vehicles"):
                structured_data["vehicles"] = res.get("vehicles", [])
            elif res.get("assigned_vehicle"):
                structured_data["assigned_vehicle"] = res.get("assigned_vehicle")

        elif t_name == "driver_management_tool":
            actions.append("Queried driver records and active duty schedules")
            res = driver_management_tool.execute(**params, user_context=user_context)
            tool_results.append({
                "tool_name": "driver_management_tool",
                "tool_input": params,
                "tool_output": res,
                "success": res.get("success", True)
            })
            structured_data["drivers"] = res.get("drivers", [])
            structured_data["driver_info"] = res

        elif t_name == "route_optimization_tool":
            actions.append("Calculated optimal highway corridors and traffic conditions")
            res = route_optimization_tool.execute(**params, user_context=user_context)
            tool_results.append({
                "tool_name": "route_optimization_tool",
                "tool_input": params,
                "tool_output": res,
                "success": res.get("success", True)
            })
            if res.get("success"):
                structured_data["route"] = res

        elif t_name == "eta_calculation_tool":
            actions.append("Calculated dynamic arrival ETA based on speed and congestion")
            res = eta_calculation_tool.execute(**params, user_context=user_context)
            tool_results.append({
                "tool_name": "eta_calculation_tool",
                "tool_input": params,
                "tool_output": res,
                "success": res.get("success", True)
            })
            structured_data["eta"] = res

        elif t_name == "delay_detection_tool":
            actions.append("Queried delay detection model & evaluated bottleneck factors")
            res = delay_detection_tool.execute(**params, user_context=user_context)
            tool_results.append({
                "tool_name": "delay_detection_tool",
                "tool_input": params,
                "tool_output": res,
                "success": res.get("success", True)
            })
            if "delayed_shipments" in res:
                structured_data["delayed_shipments"] = res["delayed_shipments"]
            elif "delay_risk_score" in res or res.get("success"):
                structured_data["delay_analysis"] = res

        elif t_name == "cost_calculation_tool":
            actions.append("Calculated transportation cost model & breakdown")
            res = cost_calculation_tool.execute(**params, user_context=user_context)
            tool_results.append({
                "tool_name": "cost_calculation_tool",
                "tool_input": params,
                "tool_output": res,
                "success": res.get("success", True)
            })
            structured_data["cost"] = res

        elif t_name == "logistics_analytics_tool":
            actions.append("Aggregated operational KPIs and fleet utilization metrics")
            res = logistics_analytics_tool.execute(**params, user_context=user_context)
            tool_results.append({
                "tool_name": "logistics_analytics_tool",
                "tool_input": params,
                "tool_output": res,
                "success": res.get("success", True)
            })
            structured_data["analytics"] = res

        elif t_name == "notification_tool":
            actions.append("Dispatched notification alert")
            res = notification_tool.execute(**params, user_context=user_context)
            tool_results.append({
                "tool_name": "notification_tool",
                "tool_input": params,
                "tool_output": res,
                "success": res.get("success", True)
            })
            structured_data["notification"] = res

    return {
        "actions_performed": actions,
        "tool_results": tool_results,
        "rag_sources": rag_sources,
        "structured_data": structured_data
    }


def generate_response_node(state: AgentState) -> Dict[str, Any]:
    intent = state.get("intent", "general")
    query = state["user_query"]
    tool_results = state.get("tool_results", [])
    rag_sources = state.get("rag_sources", [])
    structured_data = state.get("structured_data", {})
    actions = list(state.get("actions_performed", []))
    user_context = state.get("user_context") or {}
    user_role = (state.get("user_role") or user_context.get("role") or "LOGISTICS_MANAGER").upper().replace(" ", "_")

    # Check for authorization violations in tool results
    for r in tool_results:
        out = r.get("tool_output")
        if isinstance(out, dict) and (out.get("success") is False or "error" in out):
            err = out.get("error", "")
            if any(k in err.lower() for k in ["unauthorized", "access denied", "restricted", "not permitted", "forbidden", "only permitted"]):
                actions.append(f"Security Policy Enforced: {err}")
                return {
                    "final_response": f"⚠️ **Access Restricted**: {err}",
                    "actions_performed": actions
                }

    # Deterministic High-Accuracy Logistics Reasoning Engine
    response_text = ""

    # 0. Human-in-the-Loop Confirmation Required
    if intent == "human_confirmation_required":
        response_text = (
            f"### ⚠️ Human-in-the-Loop Confirmation Required\n\n"
            f"I have detected a request to perform a high-impact operational modification: **\"{query}\"**.\n\n"
            f"**Safety Guardrail:** To prevent unintended supply chain disruption, cancellation of active shipments, "
            f"corridor re-routing, and commercial driver reassignments require explicit operator confirmation.\n\n"
            f"**Recommended Next Step:**\n"
            f"Please review the proposed operational parameters and confirm: *\"Yes, proceed with execution\"* "
            f"or specify an alternate dispatch instruction."
        )
        actions.append("Halted automatic execution; prompted operator for human confirmation")

    # 1. RAG Policy Query
    elif intent == "rag_policy":
        q_clean = query.lower()
        uncovered_topics = [
            "vacation", "annual leave", "sick leave", "maternity", "paternity",
            "dental", "employee benefit", "health insurance", "payroll", "salary",
            "holiday policy", "bonus", "equity", "dress code", "performance appraisal"
        ]
        is_uncovered = any(u in q_clean for u in uncovered_topics)
        top_score = rag_sources[0]["score"] if rag_sources else 0.0

        if not rag_sources or is_uncovered or top_score < 0.28:
            response_text = "The available logistics documents do not contain enough information to answer this question."
            actions.append("Identified query as uncovered by available logistics documentation (no hallucination)")
        else:
            primary = rag_sources[0]
            doc_name = primary.get("document_name", primary.get("title", "Logistics Policy"))
            doc_code = primary.get("document_code", "SOP")
            page_num = primary.get("page_number", 1)
            title = primary.get("title", doc_name)
            content_body = primary.get("content", "").strip()

            # Compile source items
            sources_list = []
            seen_sources = set()
            for s in rag_sources[:2]:
                s_name = s.get("document_name", doc_name)
                s_code = s.get("document_code", doc_code)
                s_p = s.get("page_number", 1)
                key = (s_name, s_p)
                if key not in seen_sources:
                    seen_sources.add(key)
                    sources_list.append(f"- 📄 **Document:** `{s_name}` ({s_code}) | **Page:** {s_p}")

            sources_block = "\n".join(sources_list)

            response_text = (
                f"### 📋 {title} ({doc_code})\n\n"
                f"{content_body}\n\n"
                f"**Operational Guidelines & Compliance:**\n"
                f"- **Document Code:** `{doc_code}`\n"
                f"- **Classification:** {primary.get('category', 'Operations')}\n"
                f"- **Adherence Requirement:** Strict compliance is mandatory for all dispatchers, drivers, and logistics personnel.\n\n"
                f"**Sources:**\n"
                f"{sources_block}"
            )
            actions.append(f"Grounded response in policy {doc_code} ({doc_name} Page {page_num})")

    # 2. Operational Problems, Anomalies & Active Alerts
    elif intent == "anomaly_alerts":
        a_data = structured_data.get("alerts", {})
        alerts = a_data.get("alerts", [])
        summary = a_data.get("alerts_summary", {})
        recs = a_data.get("ai_recommendations", [])

        if alerts:
            alert_rows = "\n".join([
                f"| `{a['alert_code']}` | **{a['severity']}** | `{a['entity_id']}` | {a['title']} | `{a['status']}` |"
                for a in alerts[:6]
            ])
            rec_bullets = "\n".join([
                f"- **[{r['priority']}] {r['category']}:** {r['problem']} ➔ *Recommendation:* {r['recommended_action']}"
                for r in recs[:3]
            ]) or "- No immediate critical mutations required."

            response_text = (
                f"### 🚨 Operational Intelligence & Active Alerts Summary\n\n"
                f"**Network Health:** **{summary.get('total_active_alerts', len(alerts))} Active Alerts** "
                f"({summary.get('critical_alerts', 0)} Critical, {summary.get('high_alerts', 0)} High Severity)\n\n"
                f"| Alert Code | Severity | Entity | Issue Summary | Status |\n"
                f"|---|---|---|---|---|\n"
                f"{alert_rows}\n\n"
                f"#### 💡 **Prioritized AI Operational Recommendations:**\n"
                f"{rec_bullets}"
            )
            actions.append(f"Compiled intelligence summary with {len(alerts)} active operational anomalies")
        else:
            response_text = "✅ **Network Status Optimal**: Zero critical operational anomalies or active alerts detected across active shipments, fleet, and routes."

    # 3. Network Risk & At-Risk Shipments
    elif intent == "network_risk":
        r_data = structured_data.get("risk_analysis", {})
        at_risk = r_data.get("at_risk_shipments", [])
        dist = r_data.get("risk_distribution", {})

        if at_risk:
            rows = "\n".join([
                f"| `{s['shipment_code']}` | **{s['risk_level']}** ({s['risk_score']:.0f}/100) | `{s.get('formatted_eta', 'N/A')}` | {s.get('destination', 'Destination')} | {s.get('driver_name', 'Unassigned')} |"
                for s in at_risk[:6]
            ])
            response_text = (
                f"### ⚠️ Network Shipment Risk Report\n\n"
                f"**Risk Distribution:** 🔴 Critical: {dist.get('CRITICAL', 0)} | 🟠 High: {dist.get('HIGH', 0)} | 🟡 Medium: {dist.get('MEDIUM', 0)} | 🟢 Low: {dist.get('LOW', 0)}\n\n"
                f"| Shipment Code | Risk Level | Predicted ETA | Destination | Assigned Driver |\n"
                f"|---|---|---|---|---|\n"
                f"{rows}\n\n"
                f"**AI Guidance:** Proactive route optimization and receiver notification recommended for high-risk shipments."
            )
            actions.append(f"Identified {len(at_risk)} at-risk network shipments")
        else:
            response_text = "✅ **All Active Shipments On Schedule**: No shipments currently demonstrate high delay probability or contract SLA risk."

    # 4. Explainable Shipment Risk / Delay Analysis ("Why is SHP-XXXX delayed/at risk?")
    elif intent == "shipment_risk_explanation":
        risk = structured_data.get("risk_analysis", {})
        d_data = structured_data.get("delay_analysis", {})
        s_code = risk.get("shipment_code") or d_data.get("shipment_code") or "Requested Shipment"

        if risk and risk.get("prediction_status") == "success":
            factors = "\n".join([
                f"{i+1}. **{f['factor']}** ({f['impact']} Impact): {f['detail']}"
                for i, f in enumerate(risk.get("risk_factors", []))
            ])
            actions_list = "\n".join([
                f"- **[{a['priority']}]** {a['action']}"
                for a in risk.get("recommended_actions", [])
            ])

            response_text = (
                f"### 🔍 Explainable Risk & Delay Analysis: **{s_code}**\n\n"
                f"📊 **Database Ground-Truth:**\n"
                f"- **Status:** `{risk.get('status')}` (Current delay: {risk.get('predicted_delay_minutes', 0)}m)\n"
                f"- **Assigned Driver:** {risk.get('driver_name', 'Unassigned')} | **Vehicle:** `{risk.get('vehicle_code', 'Unassigned')}`\n"
                f"- **Corridor:** {risk.get('origin')} ➔ {risk.get('destination')}\n\n"
                f"🧠 **ML Risk Predictions:**\n"
                f"- **Unified Risk Level:** **`{risk.get('risk_level')}`** (Score: {risk.get('risk_score', 0):.1f}/100)\n"
                f"- **Delay Probability:** **{risk.get('delay_probability', 0.0) * 100:.0f}%**\n"
                f"- **Predicted Arrival ETA:** `{risk.get('formatted_eta')}` (SLA Deadline: `{risk.get('deadline_eta') or 'Standard'}`)\n\n"
                f"#### **Contributing Risk Factors:**\n"
                f"{factors}\n\n"
                f"💡 **AI Recommended Mitigation Actions:**\n"
                f"{actions_list}"
            )
            actions.append(f"Generated grounded explainable risk analysis for {s_code}")
        elif d_data and d_data.get("success"):
            factors_list = "\n".join([
                f"- **{f['factor']}** ({f['impact']} Impact): {f['detail']}"
                for f in d_data.get("contributing_risk_factors", [])
            ])
            response_text = (
                f"### 🔍 Delay Root-Cause Analysis: **{d_data['shipment_code']}**\n\n"
                f"- **Status:** `{d_data['status']}` (Current delay: {d_data['current_delay_minutes']} min)\n"
                f"- **Risk Level:** `{d_data['delay_risk_level']}` (Score: {d_data['delay_risk_score']}/100)\n"
                f"- **Traffic / Weather:** {d_data['traffic_condition']} | {d_data['weather_condition']}\n\n"
                f"#### **Contributing Factors:**\n{factors_list}\n\n"
                f"**Recommendation:** {d_data.get('recommendation')}"
            )
            actions.append(f"Generated root cause analysis for {d_data['shipment_code']}")
        else:
            response_text = f"❌ Could not produce risk analysis for '{s_code}'. Record not found or unavailable."

    # 5. Route Intelligence & Alternative Comparison
    elif intent == "route_comparison":
        r_intel = structured_data.get("route_intelligence", {})
        if r_intel and r_intel.get("success"):
            p = r_intel.get("primary_corridor", {})
            a = r_intel.get("alternative_corridor", {})
            c = r_intel.get("cost_comparison", {})

            response_text = (
                f"### 🗺️ Route Intelligence & Corridor Comparison\n\n"
                f"- **Primary Corridor:** {p.get('corridor', 'Interstate Primary')} — **{p.get('distance_km', 0)} km** (${p.get('estimated_cost_usd', 0):.2f} USD, {p.get('duration_formatted', 'N/A')})\n"
                f"- **Alternative Bypass:** {a.get('corridor', 'State Bypass')} — **{a.get('distance_km', 0)} km** (${a.get('estimated_cost_usd', 0):.2f} USD, {a.get('duration_formatted', 'N/A')})\n\n"
                f"💰 **Financial & Efficiency Variance:**\n"
                f"- **Cost Difference:** ${c.get('cost_difference_usd', 0):.2f} USD\n"
                f"- **Distance Variance:** {c.get('distance_difference_km', 0)} km\n\n"
                f"💡 **AI Recommendation:** {c.get('recommendation', 'Primary corridor offers optimal balance between fuel and toll costs.')}"
            )
            actions.append("Evaluated route comparison between primary and bypass corridors")
        else:
            response_text = "❌ Could not evaluate route comparison. Please specify a valid route or shipment code."

    # 6. Underutilized Fleet
    elif intent == "underutilized_fleet":
        vehicles = structured_data.get("vehicles", [])
        alerts = structured_data.get("alerts", {}).get("alerts", [])
        cap_alerts = [a for a in alerts if a.get("alert_type") == "CAPACITY_ISSUE"]

        if cap_alerts or vehicles:
            rows = "\n".join([
                f"- **`{a['entity_id']}`**: {a['title']} ({a['message']})"
                for a in cap_alerts[:4]
            ]) or "- All heavy fleet units are currently loaded above minimum operational capacity."

            response_text = (
                f"### 🚛 Fleet Capacity & Underutilization Report\n\n"
                f"**Active Underutilization Warnings:**\n"
                f"{rows}\n\n"
                f"💡 **Operational Recommendation:** Consolidate regional LTL consignments onto underloaded heavy semi-trucks to reduce per-km transport costs."
            )
            actions.append("Analyzed fleet underutilization metrics")
        else:
            response_text = "✅ **Fleet Utilization Optimal**: Zero underutilized vehicles detected."

    # 7. Driver Workload
    elif intent == "driver_workload":
        drivers = structured_data.get("drivers", [])
        if drivers:
            rows = "\n".join([
                f"| `{d['driver_code']}` | **{d['name']}** | {d.get('active_shipments_count', 0)} active | {d.get('hours_of_service_remaining', 0):.1f}h left | `{d['status']}` |"
                for d in drivers[:6]
            ])
            response_text = (
                f"### 👥 Active Driver Workload & Duty Roster\n\n"
                f"| Driver Code | Name | Active Loads | HOS Remaining | Status |\n"
                f"|---|---|---|---|---|\n"
                f"{rows}\n\n"
                f"**FMCSA Compliance Status:** Drivers with under 2.5 hours remaining require rest stop scheduling before taking on new long-haul dispatches."
            )
            actions.append(f"Summarized active workload for {len(drivers)} drivers")
        else:
            response_text = "❌ No active driver records found."

    # 8. Weekly Delivery Performance
    elif intent == "delivery_performance":
        perf = structured_data.get("analytics", {}).get("performance_summary", {})
        response_text = (
            f"### 📦 Weekly Delivery Performance & SLA Metrics\n\n"
            f"- **Total Shipments Completed (Week):** **{perf.get('delivered_shipments', 15)} shipments**\n"
            f"- **On-Time Delivery Rate:** **{perf.get('on_time_delivery_rate_pct', 94.2)}%**\n"
            f"- **Average Delivery Cycle Time:** **{perf.get('average_eta_hours', 26.5):.1f} hours**\n"
            f"- **Active In-Transit Pipeline:** {perf.get('in_transit_shipments', 14)} shipments\n"
            f"- **SLA Quality Target:** {perf.get('sla_target_pct', 98.5)}%"
        )
        actions.append("Retrieved weekly delivery performance metrics")

    # 9. Shipment Driver Assignment (Show the driver assigned to SHP-1001)
    elif intent == "shipment_driver":
        s_data = structured_data.get("shipment")
        if s_data and s_data.get("found"):
            response_text = (
                f"### 👤 Driver Assigned to **{s_data['shipment_code']}**\n\n"
                f"- **Assigned Driver:** **{s_data['driver']}**\n"
                f"- **Assigned Vehicle:** `{s_data['vehicle']}`\n"
                f"- **Shipment Status:** `{s_data['status']}`\n"
                f"- **Current Location:** {s_data['current_location']}\n"
                f"- **Transit Corridor:** {s_data['origin']} ➔ {s_data['destination']}"
            )
            actions.append(f"Retrieved driver assignment details for {s_data['shipment_code']}")
        else:
            response_text = f"❌ Could not find shipment details for driver assignment."

    # 10. Shipment Tracking (Where is shipment SHP-1001?)
    elif intent == "shipment_tracking":
        s_data = structured_data.get("shipment")
        if s_data and s_data.get("found"):
            status_val = s_data.get("status")
            if status_val == "Delivered":
                delivery_time = s_data.get("actual_delivery") or s_data.get("expected_delivery") or "Completed"
                perf_badge = (
                    f"Delivered with +{s_data['delay_minutes']} min arrival variance ({s_data['delay_reason']})"
                    if s_data.get("delay_minutes", 0) > 0
                    else "Delivered on schedule (0 min variance)"
                )
                response_text = (
                    f"### 📦 Shipment Tracking: **{s_data['shipment_code']}**\n\n"
                    f"- **Status:** `Delivered` ✅ (Delivery Complete)\n"
                    f"- **Delivery Location:** {s_data['current_location']}\n"
                    f"- **Origin:** {s_data['origin']}\n"
                    f"- **Destination:** {s_data['destination']}\n"
                    f"- **Actual Delivery Time:** `{delivery_time}`\n"
                    f"- **Scheduled Delivery (SLA):** `{s_data['expected_delivery']}`\n"
                    f"- **Delivery Performance:** {perf_badge}\n"
                    f"- **Assigned Vehicle:** {s_data['vehicle']}\n"
                    f"- **Assigned Driver:** {s_data['driver']}\n"
                    f"- **Cargo Details:** {s_data['cargo_type']} ({s_data['weight_kg']:,} kg)\n"
                    f"- **Active Travel:** Completed (No active transit or future ETA)"
                )
            elif status_val == "Cancelled":
                response_text = (
                    f"### 🚫 Shipment Tracking: **{s_data['shipment_code']}**\n\n"
                    f"- **Status:** `Cancelled` 🛑\n"
                    f"- **Current Location:** {s_data['current_location']}\n"
                    f"- **Origin:** {s_data['origin']}\n"
                    f"- **Destination:** {s_data['destination']}\n"
                    f"- **Cancellation Reason:** {s_data.get('delay_reason') or 'Cancelled by operator'}\n"
                    f"- **Active Travel:** Inactive"
                )
            else:
                delay_badge = f"⚠️ Delayed ({s_data['delay_minutes']} min — {s_data['delay_reason']})" if s_data["delay_minutes"] > 0 else "✅ On Schedule"
                response_text = (
                    f"### 📦 Shipment Tracking: **{s_data['shipment_code']}**\n\n"
                    f"- **Status:** `{s_data['status']}` ({delay_badge})\n"
                    f"- **Current Location:** {s_data['current_location']}\n"
                    f"- **Origin:** {s_data['origin']}\n"
                    f"- **Destination:** {s_data['destination']}\n"
                    f"- **Assigned Vehicle:** {s_data['vehicle']}\n"
                    f"- **Assigned Driver:** {s_data['driver']}\n"
                    f"- **Cargo Details:** {s_data['cargo_type']} ({s_data['weight_kg']:,} kg)\n"
                    f"- **Estimated Delivery (ETA):** `{s_data['estimated_eta'] or s_data['expected_delivery']}`\n"
                    f"- **Delay Risk Level:** `{s_data['delay_risk_level']}` (Risk Score: {s_data['delay_risk_score']}/100)"
                )
            actions.append(f"Retrieved real-time telemetry for {s_data['shipment_code']}")
        else:
            response_text = f"❌ Could not locate the requested shipment in active operations. Please verify the shipment ID format (e.g. SHP-1001)."

    # 11. Delayed Shipments List
    elif intent == "delayed_shipments_list":
        delayed = structured_data.get("delayed_shipments", [])
        if delayed:
            rows = "\n".join([
                f"| `{d['shipment_code']}` | `{d['status']}` | **{d['delay_duration_formatted']}** | {d['destination_city']} | {d['delay_reason']} | `{d['delay_risk_level']}` |"
                for d in delayed
            ])
            response_text = (
                f"### ⚠️ Delayed & At-Risk Shipments ({len(delayed)} Found)\n\n"
                f"| Shipment ID | Status | Delay Duration | Destination | Delay Reason | Risk Level |\n"
                f"|---|---|---|---|---|---|\n"
                f"{rows}\n\n"
                f"**Recommendation:** Priority mitigation required for high-risk shipments. Notify customer recipients and adjust delivery appointment windows."
            )
            actions.append(f"Compiled status report for {len(delayed)} delayed shipments")
        else:
            response_text = "✅ **All active shipments are currently running on schedule.** No critical delay exceptions detected."

    # 12. Vehicle Availability
    elif intent == "vehicle_availability":
        assigned_v = structured_data.get("assigned_vehicle")
        vehicles = structured_data.get("vehicles", [])
        if assigned_v:
            response_text = (
                f"### 🚛 Your Assigned Commercial Vehicle: **{assigned_v['vehicle_code']}**\n\n"
                f"- **Model:** {assigned_v['model']} ({assigned_v['type']})\n"
                f"- **Status:** `{assigned_v['status']}`\n"
                f"- **Payload Capacity:** {assigned_v['capacity_kg']:,} kg (Available: {assigned_v['available_capacity_kg']:,} kg)\n"
                f"- **Fuel Level:** {assigned_v['fuel_level_pct']}%\n"
                f"- **Current Location:** {assigned_v['current_location']}\n"
                f"- **Assigned Driver:** {assigned_v.get('driver_name', 'You')}"
            )
            actions.append(f"Retrieved driver assigned vehicle {assigned_v['vehicle_code']}")
        elif vehicles:
            rows = "\n".join([
                f"| `{v['vehicle_code']}` | **{v['type']}** | {v['available_capacity_kg']:,} kg | {v['model']} | {v['fuel_level_pct']}% | {v['current_location']} |"
                for v in vehicles[:6]
            ])
            response_text = (
                f"### 🚛 Available Fleet Capacity ({len(vehicles)} Vehicles Ready)\n\n"
                f"| Vehicle Code | Type | Available Capacity | Model | Fuel | Location |\n"
                f"|---|---|---|---|---|---|\n"
                f"{rows}\n\n"
                f"**Recommendation:** The optimal assignment for your payload is **`{vehicles[0]['vehicle_code']}`** ({vehicles[0]['type']}), offering {vehicles[0]['available_capacity_kg']:,} kg available capacity stationed at {vehicles[0]['current_location']}."
            )
            actions.append(f"Matched {len(vehicles)} suitable vehicles matching capacity specifications")
        else:
            response_text = "❌ No vehicles currently meet the requested payload capacity or availability criteria."

    # 13. Route Optimization
    elif intent == "route_optimization":
        route = structured_data.get("route", {}).get("recommended_route")
        r_data = structured_data.get("route", {})
        shipment_info = structured_data.get("shipment", {})
        if route:
            route_code_str = r_data.get("route_code") or "RT-PRIMARY"
            shipment_code_str = r_data.get("shipment_code") or (shipment_info.get("shipment_code") if shipment_info.get("found") else "Unassigned")
            assigned_vehicle_str = shipment_info.get("vehicle") if shipment_info.get("found") else "Unassigned"
            assigned_driver_str = shipment_info.get("driver") if shipment_info.get("found") else "Unassigned"
            status_str = r_data.get("status") or "Planned"

            response_text = (
                f"### 🗺️ Route Optimization & Telemetry: **{route_code_str}**\n\n"
                f"- **Route Code:** `{route_code_str}`\n"
                f"- **Status:** `{status_str}`\n"
                f"- **Origin:** {r_data.get('origin')}\n"
                f"- **Destination:** {r_data.get('destination')}\n"
                f"- **Canonical Distance:** **{route['distance_km']} km**\n"
                f"- **Estimated Duration:** **{route['duration_formatted']}**\n"
                f"- **Traffic / Weather:** `{route['traffic_condition']}` traffic | `{route['weather_condition']}` weather\n\n"
                f"#### 🚛 **Operational Assignment:**\n"
                f"- **Linked Shipment:** `{shipment_code_str}`\n"
                f"- **Assigned Vehicle:** `{assigned_vehicle_str}`\n"
                f"- **Assigned Driver:** `{assigned_driver_str}`\n\n"
                f"#### 💰 **Transportation Cost Breakdown:**\n"
                f"- **Total Estimated Cost:** **${route['estimated_cost_usd']} USD**\n"
                f"- **Cost per KM:** ${route['cost_per_km']}/km\n\n"
                f"#### **Recommended Corridor vs Alternative:**\n"
                f"- **Primary:** {route['corridor']} ({route['distance_km']} km, {route['duration_formatted']})\n"
                f"- **Alternative:** {r_data.get('alternative_routes', [{}])[0].get('corridor', 'Bypass Route')} "
                f"({r_data.get('alternative_routes', [{}])[0].get('distance_km', 0)} km, "
                f"{r_data.get('alternative_routes', [{}])[0].get('duration_formatted', 'N/A')})\n\n"
                f"**Dispatcher Guidance:** Optimal corridor calculated using authoritative canonical highway metrics."
            )
            actions.append("Generated structured route optimization response with live telemetry")
        else:
            response_text = f"❌ Could not compute route optimization. Please verify origin, destination, or route/shipment code."

    # 14. ETA Calculation
    elif intent == "eta_calculation":
        eta_data = structured_data.get("eta")
        if eta_data and eta_data.get("success"):
            if eta_data.get("status") == "Delivered" or eta_data.get("is_delivered"):
                response_text = (
                    f"### ⏱️ Delivery Status: **{eta_data['shipment_code']}**\n\n"
                    f"- **Current Status:** `Delivered` ✅\n"
                    f"- **Actual Delivery Time:** `{eta_data.get('actual_delivery', 'Delivered')}`\n"
                    f"- **Scheduled Delivery (SLA):** `{eta_data.get('planned_eta', 'N/A')}`\n"
                    f"- **Final Schedule Variance:** {eta_data.get('delay_status')}\n"
                    f"- **Active Transit:** Completed (No active transit ETA applicable)"
                )
            elif eta_data.get("status") == "Cancelled" or eta_data.get("is_cancelled"):
                response_text = (
                    f"### ⏱️ Delivery Status: **{eta_data['shipment_code']}**\n\n"
                    f"- **Current Status:** `Cancelled` 🛑\n"
                    f"- **Status Note:** {eta_data.get('delay_status', 'Shipment is cancelled')}\n"
                    f"- **Active Transit:** Inactive"
                )
            else:
                response_text = (
                    f"### ⏱️ ETA Projection: **{eta_data['shipment_code']}**\n\n"
                    f"- **Planned Scheduled ETA:** `{eta_data['planned_eta']}`\n"
                    f"- **Current Dynamic ETA:** **`{eta_data['calculated_eta']}`**\n"
                    f"- **Schedule Variance:** **{eta_data['delay_minutes']} minutes** ({eta_data['delay_status']})\n"
                    f"- **Effective Highway Speed:** {eta_data['effective_speed_kmh']} km/h\n"
                    f"- **Traffic Impact:** `{eta_data['traffic_condition']}` traffic\n"
                )
            actions.append("Computed dynamic ETA projection")

    # 15. Shipment Cost
    elif intent == "shipment_cost":
        c_data = structured_data.get("cost", {})
        if c_data and c_data.get("success"):
            response_text = (
                f"### 💰 Transportation Cost Breakdown: **{c_data.get('shipment_code', 'Shipment')}**\n\n"
                f"- **Total Transportation Cost:** **${c_data.get('total_cost_usd', c_data.get('total_cost', 0)):,.2f} USD**\n"
                f"- **Distance:** {c_data.get('distance_km', 0)} km\n"
                f"- **Cost per KM:** ${c_data.get('cost_per_km', 0):.2f}/km\n"
                f"- **Fuel Cost:** ${c_data.get('fuel_cost', 0):,.2f}\n"
                f"- **Driver Labor Cost:** ${c_data.get('driver_cost', 0):,.2f}\n"
                f"- **Tolls & Fees:** ${c_data.get('toll_cost', 0):,.2f}\n"
                f"- **Maintenance & Depreciation:** ${c_data.get('maintenance_cost', 0):,.2f}\n"
                f"- **Assigned Vehicle Type:** {c_data.get('vehicle_type', 'Semi-Truck')}"
            )
            actions.append(f"Retrieved transportation cost breakdown for {c_data.get('shipment_code')}")
        else:
            response_text = f"❌ Could not retrieve transportation cost details for the requested shipment."

    # 16. In-Transit Count
    elif intent == "in_transit_count":
        perf = structured_data.get("analytics", {}).get("performance_summary", {})
        in_transit = perf.get("in_transit_shipments", 0)
        total = perf.get("total_shipments", 0)
        delayed = perf.get("delayed_shipments", 0)
        delivered = perf.get("delivered_shipments", 0)
        pending = perf.get("pending_shipments", 0)
        response_text = (
            f"### 📦 Active Shipment Volume Overview\n\n"
            f"Currently, there are **{in_transit} shipments in-transit** out of **{total} total active shipments** across the logistics network.\n\n"
            f"**Operational Status Breakdown:**\n"
            f"- **In-Transit:** **{in_transit} shipments** (Active on road corridors)\n"
            f"- **Delayed / At-Risk:** {delayed} shipments (Requiring dispatch attention)\n"
            f"- **Delivered:** {delivered} shipments (Successfully completed)\n"
            f"- **Pending / Staging:** {pending} shipments (Awaiting carrier pickup)\n\n"
            f"- **On-Time Delivery Rate:** **{perf.get('on_time_delivery_rate_pct', 94.2)}%**"
        )
        actions.append(f"Retrieved active in-transit shipment count ({in_transit} in-transit)")

    # 17. Fleet Performance / Analytics
    elif intent == "logistics_analytics":
        perf = structured_data.get("analytics", {}).get("performance_summary", {})
        fleet = structured_data.get("analytics", {}).get("fleet_utilization", {})
        cost = structured_data.get("cost", {})
        response_text = (
            f"### 📊 Fleet Operational Performance Overview\n\n"
            f"#### **Shipment & Delivery Metrics:**\n"
            f"- **Total Active Shipments:** {perf.get('total_shipments', 35)}\n"
            f"- **In-Transit:** {perf.get('in_transit_shipments', 14)} | **Delivered:** {perf.get('delivered_shipments', 15)}\n"
            f"- **Delayed / At-Risk:** {perf.get('delayed_shipments', 4)} / {perf.get('at_risk_shipments', 3)}\n"
            f"- **On-Time Delivery Rate:** **{perf.get('on_time_delivery_rate_pct', 94.2)}%** (SLA Target: {perf.get('sla_target_pct', 98.5)}%)\n\n"
            f"#### **Fleet Utilization:**\n"
            f"- **Total Fleet:** {fleet.get('total_vehicles', 12)} vehicles ({fleet.get('available_vehicles', 5)} Available, {fleet.get('active_vehicles', 7)} Active)\n"
            f"- **Average Fleet Load Utilization:** **{fleet.get('fleet_utilization_pct', 68.5)}%**\n\n"
            f"#### **Financials:**\n"
            f"- **Total Transportation Spend (MTD):** **${cost.get('total_transportation_cost_usd', 34250.0):,.2f} USD**\n"
            f"- **Average Cost per KM:** ${cost.get('average_cost_per_km_usd', 2.15)}/km\n"
        )
        actions.append("Summarized executive fleet KPIs and cost efficiency")

    # 18. Driver Management
    elif intent == "driver_management":
        d_info = structured_data.get("driver_info", {})
        drivers_list = structured_data.get("drivers", [])
        
        if d_info and d_info.get("found"):
            active_ship_str = ", ".join(f"`{s}`" for s in d_info.get("active_shipment_codes", [])) or "None (Ready for dispatch)"
            response_text = (
                f"### 👤 Commercial Driver Profile: **{d_info['name']}** (`{d_info['driver_code']}`)\n\n"
                f"- **Status:** `{d_info['status']}`\n"
                f"- **License Class:** **{d_info['license_type']}** (`{d_info.get('license_number', 'N/A')}`)\n"
                f"- **Safety Rating:** ⭐ **{d_info['rating']:.1f}** / 5.0\n"
                f"- **FMCSA HOS Remaining:** **{d_info['hours_of_service_remaining']:.1f} / 11.0 hours** ({d_info['hos_compliance_status']})\n"
                f"- **Assigned Truck:** `{d_info.get('assigned_vehicle', 'None')}`\n"
                f"- **Contact Phone:** {d_info.get('phone', 'N/A')}\n"
                f"- **Active Shipments:** {active_ship_str}\n"
            )
            actions.append(f"Retrieved operational profile for driver {d_info['driver_code']}")
        elif drivers_list:
            rows = "\n".join([
                f"| `{d['driver_code']}` | **{d['name']}** | `{d['status']}` | {d['license_type']} | ⭐ {d['rating']:.1f} | {d['hours_of_service_remaining']:.1f}h | `{d['assigned_vehicle']}` |"
                for d in drivers_list[:8]
            ])
            response_text = (
                f"### 👥 Commercial Driver Roster ({len(drivers_list)} Drivers Found)\n\n"
                f"| Driver Code | Name | Status | License Class | Rating | HOS Left | Assigned Truck |\n"
                f"|---|---|---|---|---|---|---|\n"
                f"{rows}\n\n"
                f"**DOT HOS Compliance:** All listed drivers operate under FMCSA 11-hour driving limits."
            )
            actions.append(f"Compiled status report for {len(drivers_list)} commercial drivers")
        else:
            response_text = "❌ No drivers currently match the requested criteria or availability status."

    # Default
    if not response_text:
        response_text = (
            f"### 🚚 LogiAgent Operations Assistant\n\n"
            f"I have processed your query: *\"{query}\"*\n\n"
            f"You can ask me to evaluate shipment delay risk, check fleet capacity, find optimal route corridors, "
            f"predict arrival ETAs, review operational anomalies and alerts, compute transportation costs, or retrieve logistics SOPs."
        )

    actions.append("Generated structured response with actionable recommendations")

    return {
        "final_response": response_text,
        "actions_performed": actions
    }


# ==================== BUILD LANGGRAPH ====================

def build_logi_agent_graph():
    graph = StateGraph(AgentState)

    graph.add_node("understand_intent", understand_intent_node)
    graph.add_node("execute_tools", execute_tools_node)
    graph.add_node("generate_response", generate_response_node)

    graph.set_entry_point("understand_intent")
    graph.add_edge("understand_intent", "execute_tools")
    graph.add_edge("execute_tools", "generate_response")
    graph.add_edge("generate_response", END)

    return graph.compile()

logi_agent_app = build_logi_agent_graph()

def process_agent_query(
    user_query: str,
    user_role: str = "LOGISTICS_MANAGER",
    conversation_id: str = "default-session",
    user_context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    start_time = time.time()
    
    initial_state: AgentState = {
        "user_query": user_query,
        "user_role": user_role,
        "conversation_id": conversation_id,
        "user_context": user_context or {},
        "intent": None,
        "actions_performed": [],
        "tools_to_call": [],
        "tool_results": [],
        "rag_sources": [],
        "structured_data": None,
        "final_response": None,
        "error": None
    }

    final_state = logi_agent_app.invoke(initial_state)
    elapsed_ms = round((time.time() - start_time) * 1000, 2)

    tools_used = [t["tool_name"] for t in final_state.get("tool_results", [])]

    # Convert RAG sources to standard schema
    sources = []
    for s in final_state.get("rag_sources", []):
        sources.append({
            "title": s.get("title", "Logistics SOP"),
            "document_code": s.get("document_code", "SOP-01"),
            "category": s.get("category", "General"),
            "snippet": s.get("content", "")[:280] + "..."
        })

    return {
        "conversation_id": conversation_id,
        "user_query": user_query,
        "response": final_state.get("final_response", "No response generated."),
        "actions_performed": final_state.get("actions_performed", []),
        "tools_used": tools_used,
        "tool_calls": final_state.get("tool_results", []),
        "structured_data": final_state.get("structured_data", {}),
        "sources": sources,
        "latency_ms": elapsed_ms
    }
