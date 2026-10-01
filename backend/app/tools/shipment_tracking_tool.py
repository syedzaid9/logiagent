from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from app.tools.base import BaseAgentTool
from app.core.database import SessionLocal
from app.models.shipment import Shipment, ShipmentStatusHistory
from app.models.location import DeliveryLocation
from app.models.customer import Customer
from app.models.vehicle import Vehicle
from app.models.driver import Driver

class ShipmentTrackingTool(BaseAgentTool):
    name: str = "shipment_tracking_tool"
    description: str = (
        "Lookup real-time status, live coordinates, delay information, origin/destination, "
        "and route history for any shipment code (e.g. SHP-1001) or filter shipments by status."
    )
    allowed_roles = ["Admin", "Logistics Manager", "Dispatcher", "Driver", "Operations Team"]
    data_scope = "shipments"

    def execute(
        self,
        shipment_code: Optional[str] = None,
        status: Optional[str] = None,
        delayed_only: bool = False,
        user_context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        
        is_auth, err = self.check_authorization(user_context)
        if not is_auth:
            return {"found": False, "error": err}

        role = user_context.get("role") if user_context else None
        driver_id = user_context.get("driver_id") if user_context else None

        db: Session = SessionLocal()
        try:
            if shipment_code:
                code_clean = shipment_code.strip().upper()
                shipment = db.query(Shipment).filter(Shipment.shipment_code == code_clean).first()
                if not shipment:
                    # Try partial match
                    shipment = db.query(Shipment).filter(Shipment.shipment_code.like(f"%{code_clean}%")).first()

                if not shipment:
                    return {
                        "found": False,
                        "error": f"Shipment '{shipment_code}' not found in the database."
                    }

                # Driver Data Scoping Check
                from app.tools.base import normalize_role
                norm_role = normalize_role(role)
                if norm_role == "DRIVER":
                    if not driver_id:
                        email = user_context.get("email") if user_context else None
                        if email:
                            d_rec = db.query(Driver).filter(Driver.email == email).first()
                            if d_rec:
                                driver_id = d_rec.id

                    if not driver_id or shipment.driver_id != driver_id:
                        return {
                            "found": False,
                            "success": False,
                            "error": f"Unauthorized: Access denied. Shipment '{shipment.shipment_code}' is not assigned to your driver account."
                        }

                origin = db.query(DeliveryLocation).filter(DeliveryLocation.id == shipment.origin_id).first()
                destination = db.query(DeliveryLocation).filter(DeliveryLocation.id == shipment.destination_id).first()
                customer = db.query(Customer).filter(Customer.id == shipment.customer_id).first()
                vehicle = db.query(Vehicle).filter(Vehicle.id == shipment.vehicle_id).first() if shipment.vehicle_id else None
                driver = db.query(Driver).filter(Driver.id == shipment.driver_id).first() if shipment.driver_id else None
                
                history = db.query(ShipmentStatusHistory).filter(
                    ShipmentStatusHistory.shipment_id == shipment.id
                ).order_by(ShipmentStatusHistory.timestamp.asc()).all()

                is_delivered = shipment.status == "Delivered"
                is_cancelled = shipment.status == "Cancelled"
                
                # Format appropriate current location
                if is_delivered and destination:
                    current_loc = shipment.current_location_name or f"{destination.name}, {destination.city}, {destination.state}"
                else:
                    current_loc = shipment.current_location_name or (
                        f"Lat: {shipment.current_latitude:.4f}, Lng: {shipment.current_longitude:.4f}"
                        if shipment.current_latitude else "At Origin"
                    )

                return {
                    "found": True,
                    "shipment_code": shipment.shipment_code,
                    "status": shipment.status,
                    "is_delivered": is_delivered,
                    "is_cancelled": is_cancelled,
                    "is_active": shipment.status in ["In Transit", "Delayed", "Picked Up", "Assigned", "Pending"],
                    "cargo_type": shipment.cargo_type,
                    "weight_kg": shipment.weight_kg,
                    "customer_name": customer.name if customer else "N/A",
                    "origin": f"{origin.name}, {origin.city}, {origin.state}" if origin else "Unknown",
                    "destination": f"{destination.name}, {destination.city}, {destination.state}" if destination else "Unknown",
                    "vehicle": vehicle.vehicle_code if vehicle else "Unassigned",
                    "driver": driver.name if driver else "Unassigned",
                    "current_location": current_loc,
                    "current_coordinates": {
                        "latitude": shipment.current_latitude or (destination.latitude if is_delivered and destination else None),
                        "longitude": shipment.current_longitude or (destination.longitude if is_delivered and destination else None)
                    },
                    "pickup_time": shipment.pickup_time.isoformat() if shipment.pickup_time else None,
                    "expected_delivery": shipment.expected_delivery.isoformat() if shipment.expected_delivery else None,
                    "actual_delivery": shipment.actual_delivery.isoformat() if shipment.actual_delivery else None,
                    "estimated_eta": shipment.estimated_eta.isoformat() if shipment.estimated_eta else None,
                    "delay_minutes": shipment.delay_minutes,
                    "delay_reason": shipment.delay_reason or ("No delays reported" if shipment.delay_minutes == 0 else "Unspecified delay"),
                    "delay_risk_score": 0.0 if (is_delivered or is_cancelled) else shipment.delay_risk_score,
                    "delay_risk_level": "Low" if (is_delivered or is_cancelled) else shipment.delay_risk_level,
                    "history_events": [
                        {
                            "status": h.status,
                            "location": h.location_name,
                            "notes": h.notes,
                            "timestamp": h.timestamp.strftime("%Y-%m-%d %H:%M")
                        } for h in history
                    ]
                }
            
            # List query by status or delayed
            query = db.query(Shipment)
            if role == "Driver":
                if not driver_id:
                    return {"count": 0, "filter_applied": "driver_scope", "shipments": []}
                query = query.filter(Shipment.driver_id == driver_id)

            if delayed_only or (status and status.lower() == "delayed"):
                query = query.filter((Shipment.status == "Delayed") | (Shipment.delay_minutes > 0))
            elif status and status.lower() != "all":
                query = query.filter(Shipment.status.ilike(f"%{status}%"))

            shipments = query.all()
            results = []
            for s in shipments:
                dest = db.query(DeliveryLocation).filter(DeliveryLocation.id == s.destination_id).first()
                results.append({
                    "shipment_code": s.shipment_code,
                    "status": s.status,
                    "cargo_type": s.cargo_type,
                    "weight_kg": s.weight_kg,
                    "destination_city": dest.city if dest else "N/A",
                    "current_location": s.current_location_name or "In Transit",
                    "delay_minutes": s.delay_minutes,
                    "delay_reason": s.delay_reason,
                    "delay_risk_level": s.delay_risk_level
                })

            return {
                "count": len(results),
                "filter_applied": "delayed" if delayed_only else (status or "all"),
                "shipments": results
            }

        finally:
            db.close()

shipment_tracking_tool = ShipmentTrackingTool()
