from datetime import datetime, timezone
import json
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.alert import Alert
from app.models.shipment import Shipment
from app.models.route import Route
from app.models.vehicle import Vehicle
from app.models.driver import Driver
from app.models.cost import TransportationCost
from app.services.shipment_risk_service import shipment_risk_service
from app.core.logging_config import logger

class AnomalyDetectionService:
    """
    Operational Anomaly Detection & Unified Deduplicated Alert Pipeline.
    Continuously monitors live database state to surface high-priority operational issues.
    """

    def _create_or_update_alert(
        self,
        db: Session,
        alert_type: str,
        severity: str,
        entity_type: str,
        entity_id: str,
        title: str,
        message: str,
        evidence: str,
        recommended_action: str
    ) -> Alert:
        """Deduplicates active alerts; updates if existing, creates if new."""
        existing = db.query(Alert).filter(
            Alert.alert_type == alert_type,
            Alert.entity_type == entity_type,
            Alert.entity_id == entity_id,
            Alert.status == "active"
        ).first()

        if existing:
            # Update existing active alert with latest telemetry
            existing.severity = severity
            existing.message = message
            existing.evidence = evidence
            existing.recommended_action = recommended_action
            existing.updated_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(existing)
            return existing

        # Generate unique alert code
        alert_count = db.query(Alert).count() + 1
        code = f"ALT-{alert_type[:3]}-{alert_count:04d}"

        new_alert = Alert(
            alert_code=code,
            alert_type=alert_type,
            severity=severity,
            entity_type=entity_type,
            entity_id=entity_id,
            title=title,
            message=message,
            evidence=evidence,
            recommended_action=recommended_action,
            status="active",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        db.add(new_alert)
        db.commit()
        db.refresh(new_alert)
        return new_alert

    def scan_and_generate_alerts(self, db: Session) -> Dict[str, Any]:
        """
        Scans all operational entities across the database and generates/updates deduplicated alerts.
        """
        generated = []
        now_dt = datetime.now(timezone.utc)

        # 1. Scan Shipments (Delay, ETA, and Deadline risks)
        active_shipments = db.query(Shipment).filter(
            Shipment.status.in_(["Assigned", "Picked Up", "In Transit", "Delayed"])
        ).all()

        for s in active_shipments:
            risk = shipment_risk_service.analyze_shipment_risk(db, s.shipment_code)
            
            # SLA Deadline Breach Risk
            if risk.get("is_deadline_at_risk"):
                alert = self._create_or_update_alert(
                    db=db,
                    alert_type="ETA_DEADLINE_RISK",
                    severity="CRITICAL",
                    entity_type="shipment",
                    entity_id=s.shipment_code,
                    title=f"SLA Delivery Deadline Breach Risk: {s.shipment_code}",
                    message=f"Predicted ETA ({risk.get('formatted_eta')}) exceeds contract deadline for {s.shipment_code}.",
                    evidence=json.dumps(risk.get("risk_factors", [])),
                    recommended_action="Expedite shipment and re-optimize active route corridor immediately."
                )
                generated.append(alert)

            # High Delay Risk
            elif risk.get("risk_level") in ["HIGH", "CRITICAL"] or (s.delay_minutes and s.delay_minutes >= 30):
                alert = self._create_or_update_alert(
                    db=db,
                    alert_type="HIGH_DELAY_RISK",
                    severity="HIGH" if risk.get("risk_level") == "HIGH" else "CRITICAL",
                    entity_type="shipment",
                    entity_id=s.shipment_code,
                    title=f"High Delay Accumulation: {s.shipment_code}",
                    message=f"Shipment {s.shipment_code} has accumulated {s.delay_minutes or 0}m delay with risk score {risk.get('risk_score', 0):.1f}.",
                    evidence=json.dumps(risk.get("risk_factors", [])),
                    recommended_action="Review traffic bottlenecks and notify dispatch coordinator."
                )
                generated.append(alert)

        # 2. Scan Drivers (HOS Compliance)
        active_drivers = db.query(Driver).filter(Driver.status.in_(["On Duty", "Assigned"])).all()
        for d in active_drivers:
            hos = d.hours_of_service_remaining or 11.0
            if hos <= 2.0:
                alert = self._create_or_update_alert(
                    db=db,
                    alert_type="DRIVER_ISSUE",
                    severity="HIGH" if hos > 1.0 else "CRITICAL",
                    entity_type="driver",
                    entity_id=d.driver_code,
                    title=f"Driver HOS Depletion: {d.name} ({d.driver_code})",
                    message=f"Driver {d.name} has only {hos:.1f}h remaining before mandatory federal 10h rest stop.",
                    evidence=f"HOS Remaining: {hos:.1f}h, Status: {d.status}, Current Driver Code: {d.driver_code}",
                    recommended_action="Plan driver handover at next logistics hub or schedule relief driver."
                )
                generated.append(alert)

        # 3. Scan Vehicles (Capacity Underutilization & Fuel)
        active_vehicles = db.query(Vehicle).filter(Vehicle.status.in_(["Assigned", "In Transit"])).all()
        for v in active_vehicles:
            load = v.current_load_kg or 0.0
            cap = v.max_capacity_kg or 1.0
            util_pct = (load / cap) * 100.0
            if util_pct < 25.0 and cap >= 10000.0:
                alert = self._create_or_update_alert(
                    db=db,
                    alert_type="CAPACITY_ISSUE",
                    severity="MEDIUM",
                    entity_type="vehicle",
                    entity_id=v.vehicle_code,
                    title=f"Severe Fleet Underutilization: {v.vehicle_code}",
                    message=f"Heavy vehicle {v.vehicle_code} is operating at only {util_pct:.1f}% capacity ({load:.0f} / {cap:.0f} kg).",
                    evidence=f"Model: {v.model}, Max Capacity: {cap} kg, Current Load: {load} kg, Utilization: {util_pct:.1f}%",
                    recommended_action="Consolidate regional LTL loads along this transit corridor to improve cost efficiency."
                )
                generated.append(alert)

            fuel = v.fuel_level_pct or 100.0
            if fuel < 20.0:
                alert = self._create_or_update_alert(
                    db=db,
                    alert_type="VEHICLE_ISSUE",
                    severity="HIGH",
                    entity_type="vehicle",
                    entity_id=v.vehicle_code,
                    title=f"Low Fuel Warning: {v.vehicle_code}",
                    message=f"Vehicle {v.vehicle_code} fuel reserve is at {fuel:.1f}%. Refueling required promptly.",
                    evidence=f"Fuel Level: {fuel:.1f}%, Status: {v.status}",
                    recommended_action="Direct driver to authorized corridor fueling depot."
                )
                generated.append(alert)

        # 4. Scan Routes (Cost Anomalies)
        high_cost_routes = db.query(Route).filter(Route.status.in_(["Planned", "Assigned", "In Transit"])).all()
        for r in high_cost_routes:
            dist = r.planned_distance_km or 0.0
            cost = r.estimated_cost or 0.0
            if dist > 100.0:
                cost_per_km = cost / dist
                if cost_per_km > 1.45:
                    alert = self._create_or_update_alert(
                        db=db,
                        alert_type="COST_ANOMALY",
                        severity="MEDIUM",
                        entity_type="route",
                        entity_id=r.route_code,
                        title=f"Route Cost Anomaly: {r.route_code}",
                        message=f"Route {r.route_code} transportation rate (${cost_per_km:.2f}/km) exceeds standard baseline ($1.05/km).",
                        evidence=f"Planned Distance: {dist:.1f} km, Estimated Cost: ${cost:.2f} USD, Cost/KM: ${cost_per_km:.2f}",
                        recommended_action="Recalculate route using toll-free bypass corridor."
                    )
                    generated.append(alert)

        return {
            "success": True,
            "scan_completed_at": now_dt.isoformat(),
            "active_anomalies_detected": len(generated),
            "alerts": [a.to_dict() for a in generated]
        }

    def list_alerts(
        self,
        db: Session,
        status: Optional[str] = "active",
        severity: Optional[str] = None,
        entity_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Alert]:
        """Lists alerts with optional filtering and pagination."""
        query = db.query(Alert)
        if status and status.lower() != "all":
            query = query.filter(Alert.status == status.strip().lower())
        if severity and severity.lower() != "all":
            query = query.filter(Alert.severity == severity.strip().upper())
        if entity_type and entity_type.lower() != "all":
            query = query.filter(Alert.entity_type == entity_type.strip().lower())

        return query.order_by(Alert.created_at.desc()).offset(offset).limit(limit).all()

    def acknowledge_alert(self, db: Session, alert_id: int, user_email: str) -> Optional[Alert]:
        """Marks an alert as acknowledged."""
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        if not alert:
            return None
        alert.status = "acknowledged"
        alert.acknowledged_by = user_email
        alert.acknowledged_at = datetime.now(timezone.utc)
        alert.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(alert)
        return alert

    def resolve_alert(self, db: Session, alert_id: int, user_email: str) -> Optional[Alert]:
        """Marks an alert as resolved."""
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        if not alert:
            return None
        alert.status = "resolved"
        alert.resolved_at = datetime.now(timezone.utc)
        alert.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(alert)
        return alert

    def get_alerts_summary(self, db: Session) -> Dict[str, Any]:
        """Returns aggregated alert counts by status and severity."""
        active_count = db.query(Alert).filter(Alert.status == "active").count()
        critical_count = db.query(Alert).filter(Alert.status == "active", Alert.severity == "CRITICAL").count()
        high_count = db.query(Alert).filter(Alert.status == "active", Alert.severity == "HIGH").count()
        medium_count = db.query(Alert).filter(Alert.status == "active", Alert.severity == "MEDIUM").count()
        low_count = db.query(Alert).filter(Alert.status == "active", Alert.severity == "LOW").count()

        return {
            "total_active_alerts": active_count,
            "critical_alerts": critical_count,
            "high_alerts": high_count,
            "medium_alerts": medium_count,
            "low_alerts": low_count
        }

anomaly_detection_service = AnomalyDetectionService()
