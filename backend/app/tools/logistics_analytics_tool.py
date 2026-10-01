from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.tools.base import BaseAgentTool, normalize_role
from app.core.database import SessionLocal
from app.models.user import User
from app.models.driver import Driver
from app.services.analytics_service import analytics_service

class LogisticsAnalyticsTool(BaseAgentTool):
    name: str = "logistics_analytics_tool"
    description: str = (
        "Retrieve comprehensive logistics intelligence metrics, on-time delivery rates, "
        "fleet utilization, real delay root causes, operational bottlenecks, cost breakdowns, "
        "and route corridor efficiency from live PostgreSQL database."
    )
    allowed_roles = ["Admin", "Logistics Manager", "Dispatcher", "Driver", "Operations Team"]
    data_scope = "analytics"

    def execute(self, user_context: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        is_auth, err = self.check_authorization(user_context)
        if not is_auth:
            return {"success": False, "error": err}

        role_str = user_context.get("role", "Admin") if user_context else "Admin"
        driver_id = user_context.get("driver_id") if user_context else None
        email = user_context.get("email") if user_context else None
        user_id = user_context.get("user_id") if user_context else None

        db: Session = SessionLocal()
        try:
            # Build mock user or query user from DB
            user = None
            if user_id:
                user = db.query(User).filter(User.id == user_id).first()
            if not user and email:
                user = db.query(User).filter(User.email == email).first()
            
            if not user:
                # Construct transient user object with role and driver_id
                user = User(
                    email=email or "driver@logiagent.io",
                    role=role_str,
                    driver_id=driver_id
                )
            
            norm_role = normalize_role(user.role)

            # Driver Scope: strictly return driver portal telemetry
            if norm_role == "DRIVER":
                if not user.driver_id:
                    if user.email:
                        d_rec = db.query(Driver).filter(Driver.email == user.email).first()
                        if d_rec:
                            user.driver_id = d_rec.id

                if not user.driver_id:
                    return {"success": False, "error": "Driver profile not linked to account."}

                driver_rec = db.query(Driver).filter(Driver.id == user.driver_id).first()
                analytics = analytics_service.get_dashboard_analytics(db=db, user=user, time_range="30d")
                
                return {
                    "success": True,
                    "is_driver_scope": True,
                    "driver_name": driver_rec.name if driver_rec else "Driver",
                    "performance_summary": {
                        "total_assigned_shipments": analytics["kpis"]["total_shipments"],
                        "active_deliveries": analytics["kpis"]["in_transit_shipments"],
                        "completed_deliveries": analytics["kpis"]["delivered_shipments"],
                        "delayed_deliveries": analytics["kpis"]["delayed_shipments"],
                        "on_time_rate_pct": analytics["kpis"]["on_time_delivery_rate_pct"],
                        "hours_of_service_remaining": analytics["kpis"]["driver_average_hos_remaining"],
                        "performance_rating": analytics["kpis"]["driver_average_rating"]
                    },
                    "message": "Displaying personal driver operational metrics and performance rating."
                }

            # Dispatcher / Logistics Manager / Admin Scope
            time_range = kwargs.get("time_range", "30d")
            analytics = analytics_service.get_dashboard_analytics(db=db, user=user, time_range=time_range)

            result_payload = {
                "success": True,
                "performance_summary": {
                    "total_shipments": analytics["kpis"]["total_shipments"],
                    "in_transit_shipments": analytics["kpis"]["in_transit_shipments"],
                    "delivered_shipments": analytics["kpis"]["delivered_shipments"],
                    "delayed_shipments": analytics["kpis"]["delayed_shipments"],
                    "at_risk_shipments": analytics["kpis"]["at_risk_shipments"],
                    "on_time_delivery_rate_pct": analytics["kpis"]["on_time_delivery_rate_pct"],
                    "average_delivery_hours": analytics["kpis"]["average_delivery_hours"],
                    "average_delay_minutes": analytics["kpis"]["average_delay_minutes"],
                    "today_deliveries_count": analytics["kpis"]["today_deliveries_count"],
                    "sla_status": "Nominal" if analytics["kpis"]["on_time_delivery_rate_pct"] >= 90.0 else "Attention Required"
                },
                "fleet_utilization": {
                    "total_vehicles": analytics["kpis"]["total_vehicles"],
                    "active_vehicles": analytics["kpis"]["active_vehicles"],
                    "available_vehicles": analytics["kpis"]["available_vehicles"],
                    "fleet_utilization_pct": analytics["kpis"]["fleet_utilization_pct"],
                    "breakdown_by_type": analytics["vehicle_utilization"]
                },
                "driver_roster_summary": {
                    "total_drivers": analytics["kpis"]["total_drivers"],
                    "active_drivers": analytics["kpis"]["active_drivers"],
                    "available_drivers": analytics["kpis"]["available_drivers"],
                    "average_rating": analytics["kpis"]["driver_average_rating"],
                    "average_hos_remaining": analytics["kpis"]["driver_average_hos_remaining"]
                },
                "delay_root_causes": analytics["delay_root_causes"],
                "operational_bottlenecks": analytics["operational_insights"][:3]
            }

            # Financial metrics only for Admin and Logistics Manager
            if norm_role in ["ADMIN", "LOGISTICS_MANAGER"]:
                result_payload["financial_metrics"] = {
                    "total_transportation_spend_usd": analytics["kpis"]["total_transportation_cost"],
                    "average_cost_per_shipment_usd": analytics["kpis"]["average_cost_per_shipment"],
                    "average_cost_per_km_usd": analytics["kpis"]["average_cost_per_km"],
                    "cost_breakdown": analytics["cost_breakdown"]
                }

            return result_payload

        finally:
            db.close()

logistics_analytics_tool = LogisticsAnalyticsTool()
