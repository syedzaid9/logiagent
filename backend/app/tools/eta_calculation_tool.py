from datetime import datetime
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from app.tools.base import BaseAgentTool
from app.core.database import SessionLocal
from app.models.shipment import Shipment
from app.models.route import Route
from app.models.location import DeliveryLocation
from app.ml.eta_predictor import eta_predictor

class ETACalculationTool(BaseAgentTool):
    name: str = "eta_calculation_tool"
    description: str = (
        "Calculate accurate estimated time of arrival (ETA), compare planned schedule vs current projection, "
        "and calculate estimated arrival delay for in-transit shipments (e.g. SHP-1001)."
    )
    allowed_roles: List[str] = ["ADMIN", "LOGISTICS_MANAGER", "DISPATCHER", "DRIVER"]
    required_permissions: List[str] = ["eta:read", "shipments:read"]
    data_scope: str = "Scoped to driver's assigned shipments or dispatcher/manager network shipments"

    def execute(
        self,
        shipment_code: Optional[str] = None,
        traffic_condition: Optional[str] = None,
        user_context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        
        ctx = user_context or getattr(self, "user_context", None) or {}
        user_role = (ctx.get("role") or "").upper().replace(" ", "_")
        driver_id = ctx.get("driver_id")

        db: Session = SessionLocal()
        try:
            shipment = None

            # Resolve driver ID if not present in context
            if user_role == "DRIVER" and not driver_id:
                from app.models.driver import Driver
                email = ctx.get("email")
                if email:
                    d = db.query(Driver).filter(Driver.email == email).first()
                    if d:
                        driver_id = d.id

            if not shipment_code:
                if user_role == "DRIVER" and driver_id:
                    shipment = db.query(Shipment).filter(
                        Shipment.driver_id == driver_id,
                        Shipment.status.in_(["In Transit", "Delayed", "Pending", "Dispatched"])
                    ).first()
                    if not shipment:
                        shipment = db.query(Shipment).filter(Shipment.driver_id == driver_id).first()
                if not shipment:
                    return {"success": False, "error": "Shipment code is required."}
            else:
                code_clean = shipment_code.strip().upper()
                shipment = db.query(Shipment).filter(Shipment.shipment_code == code_clean).first()
                if not shipment:
                    shipment = db.query(Shipment).filter(Shipment.shipment_code.like(f"%{code_clean}%")).first()

            if not shipment:
                return {"success": False, "error": f"Shipment '{shipment_code}' not found."}

            # Security check for Driver: only permitted to query ETA for assigned shipment
            if user_role == "DRIVER" and driver_id:
                if shipment.driver_id and shipment.driver_id != driver_id:
                    return {
                        "success": False,
                        "error": "Unauthorized: You are only permitted to query ETA for your own assigned shipments."
                    }


            # 1. If shipment is already Delivered, return completed delivery telemetry
            if shipment.status == "Delivered":
                actual_time_str = shipment.actual_delivery.strftime("%Y-%m-%d %H:%M UTC") if shipment.actual_delivery else "Delivered"
                planned_time_str = shipment.expected_delivery.strftime("%Y-%m-%d %H:%M UTC") if shipment.expected_delivery else "N/A"
                delay_mins = shipment.delay_minutes
                return {
                    "success": True,
                    "shipment_code": shipment.shipment_code,
                    "status": "Delivered",
                    "is_delivered": True,
                    "planned_eta": planned_time_str,
                    "actual_delivery": actual_time_str,
                    "calculated_eta": "Delivered",
                    "delay_minutes": delay_mins,
                    "delay_status": f"Delivered (Arrival schedule variance: +{delay_mins} min)" if delay_mins > 0 else "Delivered on schedule",
                    "effective_speed_kmh": 0.0,
                    "traffic_condition": "Completed",
                    "weather_condition": "Completed",
                    "total_transit_duration_min": 0,
                    "on_time": delay_mins <= 15,
                    "message": f"Shipment {shipment.shipment_code} was delivered at {actual_time_str}."
                }

            # 2. If shipment is Cancelled
            if shipment.status == "Cancelled":
                planned_time_str = shipment.expected_delivery.strftime("%Y-%m-%d %H:%M UTC") if shipment.expected_delivery else "N/A"
                return {
                    "success": True,
                    "shipment_code": shipment.shipment_code,
                    "status": "Cancelled",
                    "is_cancelled": True,
                    "planned_eta": planned_time_str,
                    "calculated_eta": "Cancelled",
                    "delay_minutes": 0,
                    "delay_status": "Shipment cancelled by operator",
                    "effective_speed_kmh": 0.0,
                    "traffic_condition": "N/A",
                    "weather_condition": "N/A",
                    "total_transit_duration_min": 0,
                    "on_time": False,
                    "message": f"Shipment {shipment.shipment_code} has been cancelled."
                }

            # 3. Active in-transit ETA calculation using canonical route
            route = db.query(Route).filter(Route.shipment_id == shipment.id).first()
            if not route and shipment.origin_id and shipment.destination_id:
                route = db.query(Route).filter(
                    Route.origin_id == shipment.origin_id,
                    Route.destination_id == shipment.destination_id
                ).first()

            traffic = traffic_condition or (route.traffic_condition if route else "Moderate")
            weather = route.weather_condition if route else "Clear"
            
            # Canonical distance calculation
            if route and route.planned_distance_km:
                distance = route.planned_distance_km
            else:
                orig = db.query(DeliveryLocation).filter(DeliveryLocation.id == shipment.origin_id).first()
                dest = db.query(DeliveryLocation).filter(DeliveryLocation.id == shipment.destination_id).first()
                from app.services.maps_service import maps_service
                if orig and dest:
                    calc = maps_service.calculate_distance_and_duration(orig.latitude, orig.longitude, dest.latitude, dest.longitude)
                    distance = calc.get("distance_km", 450.0)
                else:
                    distance = 450.0
            
            prediction = eta_predictor.predict_eta(
                current_time=datetime.utcnow(),
                remaining_distance_km=distance,
                traffic_condition=traffic,
                weather_condition=weather,
                current_delay_min=shipment.delay_minutes
            )

            planned_time = shipment.expected_delivery
            delay_mins = shipment.delay_minutes

            status_note = (
                "On Schedule" if delay_mins == 0
                else f"Projected {delay_mins} min delay due to {shipment.delay_reason or 'transit bottlenecks'}"
            )

            return {
                "success": True,
                "shipment_code": shipment.shipment_code,
                "status": shipment.status,
                "is_delivered": False,
                "planned_eta": planned_time.strftime("%Y-%m-%d %H:%M UTC") if planned_time else "Not scheduled",
                "calculated_eta": prediction["formatted_eta"],
                "delay_minutes": delay_mins,
                "delay_status": status_note,
                "traffic_condition": traffic,
                "weather_condition": weather,
                "effective_speed_kmh": prediction["effective_speed_kmh"],
                "total_transit_duration_min": prediction["total_duration_minutes"],
                "on_time": delay_mins <= 15
            }

        finally:
            db.close()

eta_calculation_tool = ETACalculationTool()
