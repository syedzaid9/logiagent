from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from app.models.shipment import Shipment
from app.models.route import Route
from app.models.driver import Driver
from app.models.vehicle import Vehicle
from app.models.location import DeliveryLocation
from app.ml.delay_predictor import delay_predictor
from app.ml.eta_predictor import eta_predictor
from app.core.logging_config import logger

class ShipmentRiskService:
    """
    Unified Shipment Risk, Delay, and ETA Intelligence Service.
    Combines live database state, telemetry, and data-driven ML models.
    """

    def resolve_shipment(self, db: Session, identifier: str | int) -> Optional[Shipment]:
        """Looks up a shipment by ID or shipment code."""
        if isinstance(identifier, int) or (isinstance(identifier, str) and identifier.isdigit()):
            shp = db.query(Shipment).filter(Shipment.id == int(identifier)).first()
            if shp:
                return shp
        
        clean_code = str(identifier).strip().upper()
        shp = db.query(Shipment).filter(Shipment.shipment_code == clean_code).first()
        if not shp:
            shp = db.query(Shipment).filter(Shipment.shipment_code.like(f"%{clean_code}%")).first()
        return shp

    def analyze_shipment_risk(
        self,
        db: Session,
        identifier: str | int,
        user_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Calculates unified risk score, delay probability, predicted ETA,
        explainable risk factors, and recommended mitigation actions.
        """
        shipment = self.resolve_shipment(db, identifier)
        if not shipment:
            return {
                "shipment_code": str(identifier),
                "prediction_status": "prediction_unavailable",
                "error": f"Shipment '{identifier}' not found in database.",
                "risk_level": "LOW",
                "delay_probability": 0.0,
                "risk_score": 0.0,
                "predicted_eta": None,
                "risk_factors": [],
                "recommended_actions": []
            }

        # Role-based scoping check (Driver only views assigned shipments)
        if user_context:
            role = (user_context.get("role") or "").upper().replace(" ", "_")
            driver_id = user_context.get("driver_id")
            if role == "DRIVER" and driver_id and shipment.driver_id != driver_id:
                return {
                    "shipment_code": shipment.shipment_code,
                    "prediction_status": "prediction_unavailable",
                    "error": "Unauthorized: Driver accounts can only view risk analysis for assigned shipments.",
                    "risk_level": "LOW",
                    "delay_probability": 0.0,
                    "risk_score": 0.0,
                    "predicted_eta": None,
                    "risk_factors": [],
                    "recommended_actions": []
                }

        # Gather operational telemetry
        route = db.query(Route).filter(Route.shipment_id == shipment.id).first()
        driver = db.query(Driver).filter(Driver.id == shipment.driver_id).first() if shipment.driver_id else None
        vehicle = db.query(Vehicle).filter(Vehicle.id == shipment.vehicle_id).first() if shipment.vehicle_id else None
        origin = db.query(DeliveryLocation).filter(DeliveryLocation.id == shipment.origin_id).first()
        dest = db.query(DeliveryLocation).filter(DeliveryLocation.id == shipment.destination_id).first()

        distance_km = route.planned_distance_km if route and route.planned_distance_km else 450.0
        traffic = route.traffic_condition if route and route.traffic_condition else "Moderate"
        weather = route.weather_condition if route and route.weather_condition else "Clear"
        current_delay = shipment.delay_minutes or 0
        driver_hos = driver.hours_of_service_remaining if driver and driver.hours_of_service_remaining is not None else 11.0

        # ML Delay Prediction
        ml_delay = delay_predictor.predict_delay_risk(
            distance_km=distance_km,
            current_delay_min=current_delay,
            traffic_condition=traffic,
            weather_condition=weather,
            driver_hos_remaining=driver_hos,
            historical_route_delay_avg=18.0
        )

        risk_score = ml_delay.get("risk_score", 10.0)
        delay_prob = round(risk_score / 100.0, 2)
        raw_level = ml_delay.get("risk_level", "Low").upper() # LOW, MEDIUM, HIGH, CRITICAL

        # ML ETA Prediction
        now_dt = datetime.now(timezone.utc)
        eta_res = eta_predictor.predict_eta(
            current_time=now_dt,
            remaining_distance_km=distance_km,
            traffic_condition=traffic,
            weather_condition=weather,
            current_delay_min=current_delay
        )

        predicted_eta_iso = eta_res.get("predicted_eta")
        predicted_eta_dt = datetime.fromisoformat(predicted_eta_iso) if predicted_eta_iso else now_dt
        deadline_dt = shipment.expected_delivery

        is_deadline_risk = False
        if deadline_dt:
            # Handle naive/aware comparison
            if deadline_dt.tzinfo is None:
                deadline_dt = deadline_dt.replace(tzinfo=timezone.utc)
            if predicted_eta_dt > deadline_dt:
                is_deadline_risk = True
                if raw_level in ["LOW", "MEDIUM"]:
                    raw_level = "HIGH"

        # Risk Factors
        factors: List[Dict[str, Any]] = list(ml_delay.get("important_factors", []))
        if is_deadline_risk:
            delay_gap_min = int((predicted_eta_dt - deadline_dt).total_seconds() / 60)
            factors.insert(0, {
                "factor": "SLA Deadline Breach Risk",
                "impact": "Critical",
                "detail": f"Predicted arrival ({eta_res.get('formatted_eta')}) exceeds contract deadline by {max(5, delay_gap_min)} minutes."
            })

        if not driver:
            factors.append({
                "factor": "Unassigned Driver",
                "impact": "High",
                "detail": "Shipment is scheduled but has no commercial driver assigned."
            })

        # Recommended Actions
        actions: List[Dict[str, Any]] = []
        if raw_level in ["HIGH", "CRITICAL"]:
            actions.append({
                "priority": "HIGH",
                "action": "Trigger automated route optimization to bypass congested highway corridors.",
                "requires_confirmation": True
            })
            actions.append({
                "priority": "HIGH",
                "action": "Notify dispatch manager and customer receiver of predicted schedule variance.",
                "requires_confirmation": False
            })
        elif raw_level == "MEDIUM":
            actions.append({
                "priority": "MEDIUM",
                "action": "Monitor corridor rest stop telemetry and driver HOS compliance.",
                "requires_confirmation": False
            })
        else:
            actions.append({
                "priority": "LOW",
                "action": "Maintain active route corridor; telemetry indicates optimal progress.",
                "requires_confirmation": False
            })

        return {
            "shipment_id": shipment.id,
            "shipment_code": shipment.shipment_code,
            "prediction_status": "success",
            "status": shipment.status,
            "origin": f"{origin.city}, {origin.state}" if origin else "Unknown",
            "destination": f"{dest.city}, {dest.state}" if dest else "Unknown",
            "risk_level": raw_level,
            "risk_score": risk_score,
            "delay_probability": delay_prob,
            "predicted_delay_minutes": current_delay + (15 if raw_level in ["HIGH", "CRITICAL"] else 0),
            "predicted_eta": predicted_eta_iso,
            "formatted_eta": eta_res.get("formatted_eta"),
            "deadline_eta": deadline_dt.isoformat() if deadline_dt else None,
            "is_deadline_at_risk": is_deadline_risk,
            "traffic_condition": traffic,
            "weather_condition": weather,
            "driver_name": driver.name if driver else "Unassigned",
            "vehicle_code": vehicle.vehicle_code if vehicle else "Unassigned",
            "risk_factors": factors,
            "recommended_actions": actions
        }

    def predict_delay(self, db: Session, identifier: str | int, user_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Standardized delay prediction for a shipment."""
        risk_res = self.analyze_shipment_risk(db, identifier, user_context)
        return {
            "shipment_code": risk_res.get("shipment_code"),
            "prediction_status": risk_res.get("prediction_status"),
            "delay_probability": risk_res.get("delay_probability", 0.0),
            "risk_level": risk_res.get("risk_level", "LOW"),
            "predicted_delay_minutes": risk_res.get("predicted_delay_minutes", 0),
            "important_features": risk_res.get("risk_factors", [])
        }

    def predict_eta(self, db: Session, identifier: str | int, user_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Standardized ETA prediction for a shipment."""
        risk_res = self.analyze_shipment_risk(db, identifier, user_context)
        return {
            "shipment_code": risk_res.get("shipment_code"),
            "prediction_status": risk_res.get("prediction_status"),
            "predicted_eta": risk_res.get("predicted_eta"),
            "formatted_eta": risk_res.get("formatted_eta"),
            "deadline_eta": risk_res.get("deadline_eta"),
            "is_deadline_at_risk": risk_res.get("is_deadline_at_risk", False)
        }

    def get_network_risk_summary(self, db: Session, user_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Aggregates operational risk metrics across all active network shipments."""
        query = db.query(Shipment).filter(Shipment.status.in_(["Assigned", "Picked Up", "In Transit", "Delayed"]))
        
        if user_context:
            role = (user_context.get("role") or "").upper().replace(" ", "_")
            driver_id = user_context.get("driver_id")
            if role == "DRIVER" and driver_id:
                query = query.filter(Shipment.driver_id == driver_id)

        active_shipments = query.all()
        total_active = len(active_shipments)
        
        risk_counts = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
        at_risk_shipments = []

        for s in active_shipments:
            analysis = self.analyze_shipment_risk(db, s.shipment_code, user_context)
            lvl = analysis.get("risk_level", "LOW")
            risk_counts[lvl] = risk_counts.get(lvl, 0) + 1
            if lvl in ["HIGH", "CRITICAL"] or analysis.get("is_deadline_at_risk"):
                at_risk_shipments.append(analysis)

        return {
            "total_active_shipments": total_active,
            "risk_distribution": risk_counts,
            "high_risk_count": risk_counts["HIGH"] + risk_counts["CRITICAL"],
            "at_risk_shipments": at_risk_shipments[:10]
        }

shipment_risk_service = ShipmentRiskService()
