from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, require_role
from app.models.user import User
from app.models.shipment import Shipment
from app.models.route import Route
from app.models.vehicle import Vehicle
from app.models.driver import Driver
from app.models.alert import Alert
from app.schemas.ai import (
    AlertResponse,
    AlertAcknowledgeRequest,
    AlertResolveRequest,
    ShipmentRiskResponse,
    RouteAnalysisResponse,
    OperationalSummaryResponse,
    AIRecommendationItem
)
from app.services.shipment_risk_service import shipment_risk_service
from app.services.anomaly_detection_service import anomaly_detection_service
from app.services.recommendation_service import recommendation_service
from app.services.cost_service import cost_service
from app.tools.route_intelligence_tool import route_intelligence_tool
from app.core.rate_limiter import rate_limit
from app.core.config import settings

router = APIRouter(
    prefix="/ai",
    tags=["Logistics Intelligence & AI Analytics"],
    dependencies=[Depends(rate_limit(max_requests=settings.RATE_LIMIT_AI, window_seconds=60, key_prefix="ai_intel"))]
)

@router.get("/shipments/{shipment_code}/risk", response_model=ShipmentRiskResponse)
def get_shipment_risk_analysis(
    shipment_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Computes unified risk score, delay probability, predicted arrival ETA,
    and mitigation recommendations for a specific shipment.
    """
    user_ctx = {
        "user_id": current_user.id,
        "email": current_user.email,
        "role": current_user.role,
        "driver_id": current_user.driver_id
    }

    res = shipment_risk_service.analyze_shipment_risk(
        db=db,
        identifier=shipment_code,
        user_context=user_ctx
    )

    if res.get("prediction_status") == "prediction_unavailable" and "Unauthorized" in res.get("error", ""):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=res.get("error")
        )

    if res.get("prediction_status") == "prediction_unavailable" and "not found" in res.get("error", "").lower():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=res.get("error")
        )

    return res


@router.get("/routes/{route_code}/analysis", response_model=RouteAnalysisResponse)
def get_route_intelligence_analysis(
    route_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Performs corridor performance analysis, compares toll vs bypass alternatives,
    and estimates cost and risk metrics.
    """
    user_ctx = {
        "user_id": current_user.id,
        "email": current_user.email,
        "role": current_user.role,
        "driver_id": current_user.driver_id
    }

    # Data scope check for Driver role
    if current_user.role == "Driver":
        r = db.query(Route).filter(Route.route_code == route_code.strip().upper()).first()
        if r and r.shipment_id:
            shp = db.query(Shipment).filter(Shipment.id == r.shipment_id).first()
            if shp and shp.driver_id != current_user.driver_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied. Drivers can only view route intelligence for their assigned routes."
                )

    res = route_intelligence_tool.execute(
        route_code=route_code,
        compare_alternatives=True,
        user_context=user_ctx
    )

    if not res.get("success"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=res.get("error", f"Route '{route_code}' analysis failed.")
        )

    return res


@router.get("/operations/summary", response_model=OperationalSummaryResponse)
def get_operational_intelligence_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns enterprise operational intelligence KPIs, risk distribution,
    active alerts count, fleet utilization, and prioritized AI recommendations.
    """
    user_ctx = {
        "user_id": current_user.id,
        "email": current_user.email,
        "role": current_user.role,
        "driver_id": current_user.driver_id
    }

    risk_summary = shipment_risk_service.get_network_risk_summary(db=db, user_context=user_ctx)
    alerts_summary = anomaly_detection_service.get_alerts_summary(db=db)
    recs = recommendation_service.generate_recommendations(db=db, user_context=user_ctx, limit=5)

    # Compute live fleet utilization
    vehicles = db.query(Vehicle).all()
    total_cap = sum(v.max_capacity_kg or 1.0 for v in vehicles)
    total_load = sum(v.current_load_kg or 0.0 for v in vehicles)
    fleet_util = round((total_load / total_cap) * 100.0, 1) if total_cap > 0 else 0.0

    return OperationalSummaryResponse(
        total_active_shipments=risk_summary.get("total_active_shipments", 0),
        high_risk_shipments_count=risk_summary.get("high_risk_count", 0),
        active_alerts_count=alerts_summary.get("total_active_alerts", 0),
        critical_alerts_count=alerts_summary.get("critical_alerts", 0),
        fleet_utilization_pct=fleet_util,
        risk_distribution=risk_summary.get("risk_distribution", {}),
        top_recommendations=recs
    )


@router.get("/alerts", response_model=List[AlertResponse])
def list_ai_alerts(
    status: Optional[str] = Query("active", description="Filter alert status (active, acknowledged, resolved, all)"),
    severity: Optional[str] = Query(None, description="Filter severity (LOW, MEDIUM, HIGH, CRITICAL, all)"),
    entity_type: Optional[str] = Query(None, description="Filter entity type (shipment, route, vehicle, driver, all)"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves operational anomalies and alerts with deduplication and state tracking.
    """
    # Auto-scan if zero active alerts exist
    if db.query(Alert).count() == 0:
        anomaly_detection_service.scan_and_generate_alerts(db)

    alerts = anomaly_detection_service.list_alerts(
        db=db,
        status=status,
        severity=severity,
        entity_type=entity_type,
        limit=limit,
        offset=offset
    )
    return [a.to_dict() for a in alerts]


@router.post("/alerts/scan")
def trigger_anomaly_scan(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["Admin", "Logistics Manager", "Dispatcher", "Operations Team", "Fleet Manager"]))
):
    """Triggers immediate proactive scan for network anomalies and generates deduplicated alerts."""
    return anomaly_detection_service.scan_and_generate_alerts(db)


@router.post("/alerts/{alert_id}/acknowledge", response_model=AlertResponse)
def acknowledge_ai_alert(
    alert_id: int,
    req: Optional[AlertAcknowledgeRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Acknowledges an operational alert."""
    alert = anomaly_detection_service.acknowledge_alert(
        db=db,
        alert_id=alert_id,
        user_email=current_user.email
    )
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert ID {alert_id} not found."
        )
    return alert.to_dict()


@router.post("/alerts/{alert_id}/resolve", response_model=AlertResponse)
def resolve_ai_alert(
    alert_id: int,
    req: Optional[AlertResolveRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["Admin", "Logistics Manager", "Dispatcher", "Operations Team", "Fleet Manager"]))
):
    """Resolves an operational alert."""
    alert = anomaly_detection_service.resolve_alert(
        db=db,
        alert_id=alert_id,
        user_email=current_user.email
    )
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert ID {alert_id} not found."
        )
    return alert.to_dict()


@router.get("/recommendations", response_model=List[AIRecommendationItem])
def get_operational_recommendations(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns prioritized operational mitigation recommendations with human confirmation requirements.
    """
    user_ctx = {
        "user_id": current_user.id,
        "email": current_user.email,
        "role": current_user.role,
        "driver_id": current_user.driver_id
    }
    return recommendation_service.generate_recommendations(
        db=db,
        user_context=user_ctx,
        limit=limit
    )
