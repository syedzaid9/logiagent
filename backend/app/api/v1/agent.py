from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from app.api.deps import get_current_user
from app.core.permissions import get_role_permissions
from app.models.user import User
from app.models.driver import Driver
from app.models.vehicle import Vehicle
from app.core.database import SessionLocal
from app.schemas.agent import (
    AgentChatRequest,
    AgentChatResponse,
    AgentCapabilitiesResponse,
    SuggestedPrompt
)
from app.agents import process_agent_query
from app.core.logging_config import logger
from app.core.rate_limiter import rate_limit
from app.core.config import settings

router = APIRouter(
    prefix="/agent",
    tags=["LogiAgent AI Assistant"],
    dependencies=[Depends(rate_limit(max_requests=settings.RATE_LIMIT_AI, window_seconds=60, key_prefix="agent_ai"))]
)
assistant_router = APIRouter(
    prefix="/assistant",
    tags=["LogiAgent AI Assistant"],
    dependencies=[Depends(rate_limit(max_requests=settings.RATE_LIMIT_AI, window_seconds=60, key_prefix="agent_ai"))]
)

def get_role_capabilities(current_user: User) -> AgentCapabilitiesResponse:
    raw_role = current_user.role or "Logistics Manager"
    role_norm = raw_role.upper().replace(" ", "_")
    permissions = get_role_permissions(current_user.role)
    
    operational_scope: Dict[str, Any] = {}
    driver_id = getattr(current_user, "driver_id", None)

    db = SessionLocal()
    try:
        if role_norm == "DRIVER":
            d = None
            if driver_id:
                d = db.query(Driver).filter(Driver.id == driver_id).first()
            if not d and current_user.email:
                d = db.query(Driver).filter(Driver.email == current_user.email).first()
            if d:
                driver_id = d.id
                v_code = None
                if d.current_vehicle_id:
                    v = db.query(Vehicle).filter(Vehicle.id == d.current_vehicle_id).first()
                    v_code = v.vehicle_code if v else None
                operational_scope = {
                    "driver_id": d.id,
                    "driver_code": d.driver_code,
                    "name": d.name,
                    "status": d.status,
                    "assigned_vehicle": v_code,
                    "license_type": d.license_type,
                    "hours_of_service_remaining": d.hours_of_service_remaining
                }
    finally:
        db.close()

    # Dynamic role-tailored capabilities and prompts (NO hardcoded IDs)
    if role_norm == "DRIVER":
        allowed_tools = [
            "shipment_tracking_tool",
            "vehicle_availability_tool",
            "driver_management_tool",
            "route_optimization_tool",
            "eta_calculation_tool",
            "delay_detection_tool",
            "notification_tool",
            "rag_policy_retriever"
        ]
        allowed_docs = ["DRIVER", "PUBLIC_OPERATIONAL"]
        prompts = [
            SuggestedPrompt(label="My Next Shipment", query="Where is my next shipment and delivery schedule?", category="Shipments"),
            SuggestedPrompt(label="My Assigned Vehicle", query="What vehicle is assigned to me?", category="Vehicle"),
            SuggestedPrompt(label="My Route & Navigation", query="What is the optimal route for my active shipment?", category="Route"),
            SuggestedPrompt(label="My Arrival ETA", query="Calculate dynamic arrival ETA for my delivery", category="ETA"),
            SuggestedPrompt(label="Driver Safety SOP", query="Show standard safety procedures and hours of service rules", category="SOP"),
            SuggestedPrompt(label="Hazmat Guidelines", query="What is the protocol for handling hazardous materials cargo?", category="Compliance")
        ]
    elif role_norm == "DISPATCHER":
        allowed_tools = [
            "shipment_tracking_tool",
            "vehicle_availability_tool",
            "driver_management_tool",
            "route_optimization_tool",
            "eta_calculation_tool",
            "delay_detection_tool",
            "notification_tool",
            "rag_policy_retriever"
        ]
        allowed_docs = ["DISPATCHER", "DRIVER", "PUBLIC_OPERATIONAL"]
        operational_scope = {"dispatch_zone": "All Corridors", "active_dispatch": True}
        prompts = [
            SuggestedPrompt(label="Delayed Shipments", query="Show all delayed and at-risk shipments requiring attention", category="Operations"),
            SuggestedPrompt(label="Available Vehicles", query="Which vehicles are available for 2000 kg cargo payload?", category="Fleet"),
            SuggestedPrompt(label="Driver Roster & HOS", query="Show available drivers and remaining hours of service", category="Dispatch"),
            SuggestedPrompt(label="Route Optimization", query="Calculate fastest route for primary highway corridors", category="Corridors"),
            SuggestedPrompt(label="Loading & Detention SOP", query="What are the procedures for warehouse loading and detention fees?", category="SOP"),
            SuggestedPrompt(label="Alert Ops Team", query="Notify operations team about high-risk delivery bottlenecks", category="Alerts")
        ]
    elif role_norm == "LOGISTICS_MANAGER":
        allowed_tools = [
            "shipment_tracking_tool",
            "vehicle_availability_tool",
            "driver_management_tool",
            "route_optimization_tool",
            "eta_calculation_tool",
            "delay_detection_tool",
            "cost_calculation_tool",
            "logistics_analytics_tool",
            "notification_tool",
            "rag_policy_retriever"
        ]
        allowed_docs = ["MANAGER", "DISPATCHER", "DRIVER", "PUBLIC_OPERATIONAL"]
        operational_scope = {"management_scope": "Full Logistics Operations", "cost_access": True}
        prompts = [
            SuggestedPrompt(label="Fleet Performance", query="How is our fleet performing this month?", category="Analytics"),
            SuggestedPrompt(label="Transportation Spend", query="What is our total transportation spend and cost per km?", category="Financials"),
            SuggestedPrompt(label="Delay Root-Cause Analysis", query="What are the main causes of active shipment delays?", category="Performance"),
            SuggestedPrompt(label="Fleet Utilization", query="Show fleet capacity utilization and available trucks", category="Capacity"),
            SuggestedPrompt(label="Active In-Transit Volume", query="How many shipments are currently in transit?", category="Operations"),
            SuggestedPrompt(label="Cold Chain Protocol", query="What are the temperature monitoring procedures for reefer transport?", category="SOP")
        ]
    else: # ADMIN
        allowed_tools = [
            "shipment_tracking_tool",
            "vehicle_availability_tool",
            "driver_management_tool",
            "route_optimization_tool",
            "eta_calculation_tool",
            "delay_detection_tool",
            "cost_calculation_tool",
            "logistics_analytics_tool",
            "notification_tool",
            "rag_policy_retriever"
        ]
        allowed_docs = ["ADMIN", "MANAGER", "DISPATCHER", "DRIVER", "PUBLIC_OPERATIONAL"]
        operational_scope = {"admin_scope": "Full Enterprise System Access", "all_permissions": True}
        prompts = [
            SuggestedPrompt(label="Logistics Performance KPIs", query="Show full logistics performance overview and fleet metrics", category="Executive"),
            SuggestedPrompt(label="Transportation Cost Audit", query="Audit total transportation spend and cost breakdown", category="Financials"),
            SuggestedPrompt(label="Network Delay Exceptions", query="Show all delayed and at-risk shipments across the network", category="Operations"),
            SuggestedPrompt(label="Fleet Capacity Overview", query="Show fleet capacity utilization and available vehicles", category="Fleet"),
            SuggestedPrompt(label="Security & Compliance SOP", query="What are the corporate compliance and data governance policies?", category="Compliance")
        ]

    return AgentCapabilitiesResponse(
        role=raw_role,
        user_name=current_user.full_name or current_user.email,
        user_email=current_user.email,
        permissions=permissions,
        allowed_tools=allowed_tools,
        allowed_document_categories=allowed_docs,
        operational_scope=operational_scope,
        suggested_prompts=prompts
    )


@router.get("/capabilities", response_model=AgentCapabilitiesResponse)
@assistant_router.get("/capabilities", response_model=AgentCapabilitiesResponse)
def get_capabilities(current_user: User = Depends(get_current_user)):
    return get_role_capabilities(current_user)


@router.post("/chat", response_model=AgentChatResponse)
@router.post("/query", response_model=AgentChatResponse)
@assistant_router.post("/chat", response_model=AgentChatResponse)
@assistant_router.post("/query", response_model=AgentChatResponse)
def agent_chat(
    req: AgentChatRequest,
    current_user: User = Depends(get_current_user)
):
    if not req.message.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message cannot be empty."
        )

    raw_role = current_user.role or "Logistics Manager"
    role_norm = raw_role.upper().replace(" ", "_")
    conv_id = req.conversation_id or f"session-user-{current_user.id}"

    driver_id = getattr(current_user, "driver_id", None)
    if role_norm == "DRIVER":
        db = SessionLocal()
        try:
            if not driver_id and current_user.email:
                d = db.query(Driver).filter(Driver.email == current_user.email).first()
                if d:
                    driver_id = d.id
        finally:
            db.close()

    user_context = {
        "user_id": current_user.id,
        "auth_user_id": current_user.auth_user_id,
        "email": current_user.email,
        "role": role_norm,
        "permissions": get_role_permissions(current_user.role),
        "operational_profile_id": driver_id,
        "driver_id": driver_id
    }

    logger.info(f"Processing agent query from user [{current_user.email}] role [{role_norm}]: '{req.message}'")

    try:
        result = process_agent_query(
            user_query=req.message,
            user_role=role_norm,
            conversation_id=conv_id,
            user_context=user_context
        )
        return AgentChatResponse(**result)
    except Exception as e:
        logger.error(f"Error processing agent query: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent execution error: {str(e)}"
        )

