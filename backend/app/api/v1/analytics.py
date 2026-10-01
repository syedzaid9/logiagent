import csv
import io
from typing import Dict, Any, List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.driver import Driver
from app.models.vehicle import Vehicle
from app.models.shipment import Shipment
from app.models.route import Route
from app.services.analytics_service import analytics_service
from app.tools.base import normalize_role

router = APIRouter(prefix="/analytics", tags=["Analytics & Logistics Intelligence"])

@router.get("/driver-portal")
def get_driver_portal_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    norm_role = normalize_role(current_user.role)
    if norm_role != "DRIVER" or not current_user.driver_id:
        # Fallback to email search if driver_id not set on user model
        if current_user.email:
            d_found = db.query(Driver).filter(Driver.email == current_user.email).first()
            if d_found:
                current_user.driver_id = d_found.id
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Current user is not linked to an active driver profile."
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current user is not linked to an active driver profile."
            )

    driver = db.query(Driver).filter(Driver.id == current_user.driver_id).first()
    if not driver:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver profile not found.")

    vehicle = db.query(Vehicle).filter(Vehicle.id == driver.current_vehicle_id).first() if driver.current_vehicle_id else None

    # Driver's assigned shipments
    shipments = db.query(Shipment).filter(Shipment.driver_id == driver.id).order_by(Shipment.created_at.desc()).all()
    active_shipments = [s for s in shipments if s.status in ["Assigned", "Picked Up", "In Transit", "Delayed", "Created", "Pending"]]
    if not active_shipments and shipments:
        active_shipments = [s for s in shipments if s.status != "Cancelled"]
    completed_shipments = [s for s in shipments if s.status == "Delivered"]

    # Active route
    active_route = None
    if active_shipments:
        primary_shp = active_shipments[0]
        active_route = db.query(Route).filter(Route.shipment_id == primary_shp.id).first()

    return {
        "driver": {
            "id": driver.id,
            "driver_code": driver.driver_code,
            "name": driver.name,
            "email": driver.email,
            "phone": driver.phone,
            "license_number": driver.license_number,
            "license_type": driver.license_type,
            "status": driver.status,
            "rating": driver.rating or 4.8,
            "hours_of_service_remaining": driver.hours_of_service_remaining or 11.0
        },
        "vehicle": {
            "id": vehicle.id,
            "vehicle_code": vehicle.vehicle_code,
            "model": vehicle.model,
            "type": vehicle.type,
            "status": vehicle.status,
            "current_location": vehicle.current_location,
            "current_load_kg": vehicle.current_load_kg,
            "max_capacity_kg": vehicle.max_capacity_kg,
            "utilization_pct": round((vehicle.current_load_kg / vehicle.max_capacity_kg) * 100.0, 1) if vehicle and vehicle.max_capacity_kg > 0 else 0.0
        } if vehicle else None,
        "kpis": {
            "total_assigned": len(shipments),
            "active_deliveries": len(active_shipments),
            "completed_deliveries": len(completed_shipments),
            "hours_of_service_remaining": driver.hours_of_service_remaining or 11.0,
            "performance_rating": driver.rating or 4.8
        },
        "active_shipments": [
            {
                "id": s.id,
                "shipment_code": s.shipment_code,
                "status": s.status,
                "cargo_type": s.cargo_type,
                "weight_kg": s.weight_kg,
                "origin_hub": s.current_location_name or "Origin Facility",
                "estimated_eta": s.estimated_eta.isoformat() if s.estimated_eta else None,
                "delay_minutes": s.delay_minutes or 0,
                "delay_risk_level": s.delay_risk_level or "Low"
            } for s in active_shipments
        ],
        "active_route": {
            "route_code": active_route.route_code,
            "planned_distance_km": active_route.planned_distance_km,
            "planned_duration_min": active_route.planned_duration_min,
            "traffic_condition": active_route.traffic_condition or "Normal",
            "weather_condition": active_route.weather_condition or "Clear"
        } if active_route else None
    }

@router.get("/dashboard")
def get_analytics_dashboard(
    time_range: str = Query("30d", description="Time range: today, yesterday, 7d, 30d, 90d, custom"),
    start_date: Optional[str] = Query(None, description="Custom start date (ISO string)"),
    end_date: Optional[str] = Query(None, description="Custom end date (ISO string)"),
    status: Optional[str] = Query(None, description="Filter by shipment status"),
    vehicle_id: Optional[int] = Query(None, description="Filter by vehicle ID"),
    driver_id: Optional[int] = Query(None, description="Filter by driver ID"),
    customer_id: Optional[int] = Query(None, description="Filter by customer ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    filters = {
        "status": status,
        "vehicle_id": vehicle_id,
        "driver_id": driver_id,
        "customer_id": customer_id
    }
    return analytics_service.get_dashboard_analytics(
        db=db,
        user=current_user,
        time_range=time_range,
        start_date_str=start_date,
        end_date_str=end_date,
        filters=filters
    )

@router.get("/kpis")
def get_kpi_summary(
    time_range: str = Query("30d"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    analytics = analytics_service.get_dashboard_analytics(db=db, user=current_user, time_range=time_range)
    return {
        "kpis": analytics["kpis"],
        "user_role": current_user.role,
        "time_range": time_range
    }

@router.get("/insights")
def get_operational_insights(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    analytics = analytics_service.get_dashboard_analytics(db=db, user=current_user, time_range="30d")
    return {
        "insights": analytics["operational_insights"],
        "total_insights": len(analytics["operational_insights"]),
        "generated_at": datetime.utcnow().isoformat()
    }

@router.get("/export")
def export_analytics_csv(
    time_range: str = Query("30d"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    analytics = analytics_service.get_dashboard_analytics(db=db, user=current_user, time_range=time_range)
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Section 1: Executive KPIs
    writer.writerow(["LogiAgent Logistics Intelligence Export"])
    writer.writerow(["Generated At", datetime.utcnow().isoformat()])
    writer.writerow(["User Role", current_user.role])
    writer.writerow(["Time Range", time_range])
    writer.writerow([])
    
    writer.writerow(["Metric", "Value"])
    for k, v in analytics["kpis"].items():
        writer.writerow([k, v])
    writer.writerow([])

    # Section 2: Delay Root Causes
    writer.writerow(["Delay Root Causes Breakdown"])
    writer.writerow(["Reason", "Occurrences", "Percentage"])
    for r in analytics.get("delay_root_causes", []):
        writer.writerow([r["reason"], r["count"], f"{r['percentage']}%"])
    writer.writerow([])

    # Section 3: Cost Modeling (if authorized)
    norm_role = normalize_role(current_user.role)
    if norm_role in ["ADMIN", "LOGISTICS_MANAGER"]:
        writer.writerow(["Cost Breakdown by Category"])
        writer.writerow(["Category", "Amount ($ USD)", "Percentage"])
        for c in analytics.get("cost_breakdown", []):
            writer.writerow([c["category"], c["amount"], f"{c['percentage']}%"])
        writer.writerow([])

    output.seek(0)
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=logiagent_analytics_{time_range}_{datetime.utcnow().strftime('%Y%m%d')}.csv"}
    )
