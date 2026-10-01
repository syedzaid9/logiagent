from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from app.tools.base import BaseAgentTool
from app.core.database import SessionLocal
from app.models.shipment import Shipment
from app.models.driver import Driver
from app.models.route import Route
from app.models.location import DeliveryLocation
from app.ml.delay_predictor import delay_predictor

class DelayDetectionTool(BaseAgentTool):
    name: str = "delay_detection_tool"
    description: str = (
        "Detect all delayed shipments, identify at-risk shipments before delays occur, "
        "calculate delay durations, and explain root causes (e.g. why SHP-1001 is delayed)."
    )
    allowed_roles: List[str] = ["ADMIN", "LOGISTICS_MANAGER", "DISPATCHER", "DRIVER"]
    required_permissions: List[str] = ["delays:read", "shipments:read"]
    data_scope: str = "Scoped to driver's assigned shipments or dispatcher/manager network shipments"

    def execute(
        self,
        shipment_code: Optional[str] = None,
        min_delay_minutes: int = 0,
        at_risk_only: bool = False,
        user_context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        
        ctx = user_context or getattr(self, "user_context", None) or {}
        user_role = (ctx.get("role") or "").upper().replace(" ", "_")
        driver_id = ctx.get("driver_id")

        db: Session = SessionLocal()
        try:
            # Resolve driver ID if driver
            if user_role == "DRIVER" and not driver_id:
                email = ctx.get("email")
                if email:
                    d = db.query(Driver).filter(Driver.email == email).first()
                    if d:
                        driver_id = d.id

            if shipment_code:
                code_clean = shipment_code.strip().upper()
                shipment = db.query(Shipment).filter(Shipment.shipment_code == code_clean).first()
                if not shipment:
                    shipment = db.query(Shipment).filter(Shipment.shipment_code.like(f"%{code_clean}%")).first()

                if not shipment:
                    return {"success": False, "error": f"Shipment '{shipment_code}' not found."}

                # Driver parameter verification
                if user_role == "DRIVER" and driver_id:
                    if shipment.driver_id and shipment.driver_id != driver_id:
                        return {
                            "success": False,
                            "error": "Unauthorized: You are only permitted to check delay details for your own assigned shipments."
                        }

                route = db.query(Route).filter(Route.shipment_id == shipment.id).first()
                driver = db.query(Driver).filter(Driver.id == shipment.driver_id).first() if shipment.driver_id else None
                origin = db.query(DeliveryLocation).filter(DeliveryLocation.id == shipment.origin_id).first()
                destination = db.query(DeliveryLocation).filter(DeliveryLocation.id == shipment.destination_id).first()

                distance = route.planned_distance_km if route else 450.0
                traffic = route.traffic_condition if route else "Moderate"
                weather = route.weather_condition if route else "Clear"
                hos = driver.hours_of_service_remaining if driver else 11.0

                ml_risk = delay_predictor.predict_delay_risk(
                    distance_km=distance,
                    current_delay_min=shipment.delay_minutes,
                    traffic_condition=traffic,
                    weather_condition=weather,
                    driver_hos_remaining=hos
                )

                return {
                    "success": True,
                    "shipment_code": shipment.shipment_code,
                    "status": shipment.status,
                    "current_delay_minutes": shipment.delay_minutes,
                    "delay_reason": shipment.delay_reason or "No delay currently logged",
                    "origin": f"{origin.city}, {origin.state}" if origin else "Unknown",
                    "destination": f"{destination.city}, {destination.state}" if destination else "Unknown",
                    "traffic_condition": traffic,
                    "weather_condition": weather,
                    "driver_hos_remaining": hos,
                    "delay_risk_score": ml_risk["risk_score"],
                    "delay_risk_level": ml_risk["risk_level"],
                    "contributing_risk_factors": ml_risk["important_factors"],
                    "recommendation": ml_risk["mitigation_recommendation"]
                }

            # Batch query for delayed or at-risk shipments
            query = db.query(Shipment)

            # Restrict driver to own shipments
            if user_role == "DRIVER":
                if driver_id:
                    query = query.filter(Shipment.driver_id == driver_id)
                else:
                    return {
                        "success": True,
                        "delayed_count": 0,
                        "filter": "driver_assigned",
                        "delayed_shipments": []
                    }

            if at_risk_only:
                query = query.filter((Shipment.delay_risk_score >= 50.0) | (Shipment.delay_risk_level.in_(["High", "Critical"])))
            else:
                query = query.filter((Shipment.delay_minutes > min_delay_minutes) | (Shipment.status == "Delayed"))


            delayed_shipments = query.all()
            results = []
            for s in delayed_shipments:
                dest = db.query(DeliveryLocation).filter(DeliveryLocation.id == s.destination_id).first()
                results.append({
                    "shipment_code": s.shipment_code,
                    "status": s.status,
                    "delay_minutes": s.delay_minutes,
                    "delay_duration_formatted": f"{s.delay_minutes // 60}h {s.delay_minutes % 60}m" if s.delay_minutes > 0 else "0m",
                    "delay_reason": s.delay_reason or "Congestion / Processing delay",
                    "destination_city": dest.city if dest else "N/A",
                    "delay_risk_score": s.delay_risk_score,
                    "delay_risk_level": s.delay_risk_level
                })

            return {
                "success": True,
                "delayed_count": len(results),
                "filter": "at_risk" if at_risk_only else f"delayed_over_{min_delay_minutes}min",
                "delayed_shipments": results
            }

        finally:
            db.close()

delay_detection_tool = DelayDetectionTool()
