from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from app.tools.base import BaseAgentTool
from app.core.database import SessionLocal
from app.models.driver import Driver
from app.models.vehicle import Vehicle
from app.models.shipment import Shipment

class DriverManagementTool(BaseAgentTool):
    name: str = "driver_management_tool"
    description: str = (
        "Query driver availability, check remaining Hours of Service (HOS), "
        "inspect driver licenses/ratings, and view active vehicle/shipment assignments."
    )
    allowed_roles = ["Admin", "Logistics Manager", "Dispatcher", "Driver", "Operations Team"]
    data_scope = "drivers"

    def execute(
        self,
        driver_name: Optional[str] = None,
        driver_code: Optional[str] = None,
        vehicle_code: Optional[str] = None,
        available_only: bool = False,
        active_only: bool = False,
        min_hos_remaining: Optional[float] = None,
        user_context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        
        is_auth, err = self.check_authorization(user_context)
        if not is_auth:
            return {"found": False, "error": err}

        role = user_context.get("role") if user_context else None
        user_driver_id = user_context.get("driver_id") if user_context else None
        from app.tools.base import normalize_role
        norm_role = normalize_role(role)

        db: Session = SessionLocal()
        try:
            # Driver Scope Verification
            if norm_role == "DRIVER":
                if not user_driver_id:
                    email = user_context.get("email") if user_context else None
                    if email:
                        d_rec = db.query(Driver).filter(Driver.email == email).first()
                        if d_rec:
                            user_driver_id = d_rec.id

                if not user_driver_id:
                    return {"success": False, "found": False, "error": "Your driver account is not linked to an active driver profile."}
                
                driver = db.query(Driver).filter(Driver.id == user_driver_id).first()
                if not driver:
                    return {"success": False, "found": False, "error": "Driver profile record not found."}

                # If asking for a specific other driver, block access
                if driver_code and driver.driver_code.upper() != driver_code.strip().upper():
                    return {
                        "success": False,
                        "found": False,
                        "error": f"Access denied. You are only authorized to view your own driver profile ({driver.driver_code})."
                    }
                if driver_name and driver.name.lower() != driver_name.strip().lower() and driver_name.strip().lower() not in driver.name.lower():
                    return {
                        "success": False,
                        "found": False,
                        "error": f"Access denied. You are only authorized to view your own driver profile ({driver.name})."
                    }

                vehicle = db.query(Vehicle).filter(Vehicle.id == driver.current_vehicle_id).first() if driver.current_vehicle_id else None
                active_shipments = db.query(Shipment).filter(
                    Shipment.driver_id == driver.id,
                    Shipment.status.in_(["Assigned", "Picked Up", "In Transit", "Delayed"])
                ).all()

                return {
                    "success": True,
                    "found": True,
                    "is_own_profile": True,
                    "driver_code": driver.driver_code,
                    "name": driver.name,
                    "phone": driver.phone,
                    "email": driver.email,
                    "status": driver.status,
                    "rating": driver.rating,
                    "license_type": driver.license_type,
                    "license_number": driver.license_number,
                    "hours_of_service_remaining": driver.hours_of_service_remaining,
                    "assigned_vehicle": vehicle.vehicle_code if vehicle else "None",
                    "assigned_vehicle_model": vehicle.model if vehicle else "None",
                    "active_shipments_count": len(active_shipments),
                    "active_shipment_codes": [s.shipment_code for s in active_shipments],
                    "hos_compliance_status": "Compliant" if (driver.hours_of_service_remaining or 11.0) > 2.0 else "Rest Required Soon",
                    "message": "Displaying your personal commercial driver profile and duty status."
                }

            # Dispatcher, Manager, Admin driver query
            if vehicle_code:
                v = db.query(Vehicle).filter(Vehicle.vehicle_code.ilike(f"%{vehicle_code.strip()}%")).first()
                if not v:
                    return {"found": False, "error": f"Vehicle '{vehicle_code}' not found."}
                if not v.driver_id:
                    return {"found": False, "error": f"Vehicle '{v.vehicle_code}' has no assigned driver."}
                
                driver = db.query(Driver).filter(Driver.id == v.driver_id).first()
                if not driver:
                    return {"found": False, "error": f"Driver ID {v.driver_id} not found."}
                
                active_shipments = db.query(Shipment).filter(
                    Shipment.driver_id == driver.id,
                    Shipment.status.in_(["Assigned", "Picked Up", "In Transit", "Delayed"])
                ).all()

                return {
                    "found": True,
                    "driver_code": driver.driver_code,
                    "name": driver.name,
                    "phone": driver.phone,
                    "email": driver.email,
                    "status": driver.status,
                    "rating": driver.rating,
                    "license_type": driver.license_type,
                    "license_number": driver.license_number,
                    "hours_of_service_remaining": driver.hours_of_service_remaining,
                    "assigned_vehicle": v.vehicle_code,
                    "assigned_vehicle_model": v.model,
                    "active_shipments_count": len(active_shipments),
                    "active_shipment_codes": [s.shipment_code for s in active_shipments],
                    "hos_compliance_status": "Compliant" if (driver.hours_of_service_remaining or 11.0) > 2.0 else "Rest Required Soon"
                }

            # Query single driver by code or name
            if driver_code or driver_name:
                query = db.query(Driver)
                if driver_code:
                    query = query.filter(Driver.driver_code.ilike(f"%{driver_code.strip()}%"))
                elif driver_name:
                    query = query.filter(Driver.name.ilike(f"%{driver_name.strip()}%"))

                driver = query.first()
                if not driver:
                    return {"found": False, "error": f"Driver '{driver_code or driver_name}' not found."}

                vehicle = db.query(Vehicle).filter(Vehicle.id == driver.current_vehicle_id).first() if driver.current_vehicle_id else None
                active_shipments = db.query(Shipment).filter(
                    Shipment.driver_id == driver.id,
                    Shipment.status.in_(["Assigned", "Picked Up", "In Transit", "Delayed"])
                ).all()

                return {
                    "found": True,
                    "driver_code": driver.driver_code,
                    "name": driver.name,
                    "phone": driver.phone,
                    "email": driver.email,
                    "status": driver.status,
                    "rating": driver.rating,
                    "license_type": driver.license_type,
                    "license_number": driver.license_number,
                    "hours_of_service_remaining": driver.hours_of_service_remaining,
                    "assigned_vehicle": vehicle.vehicle_code if vehicle else "None",
                    "assigned_vehicle_model": vehicle.model if vehicle else "None",
                    "active_shipments_count": len(active_shipments),
                    "active_shipment_codes": [s.shipment_code for s in active_shipments],
                    "hos_compliance_status": "Compliant" if (driver.hours_of_service_remaining or 11.0) > 2.0 else "Rest Required Soon"
                }

            # List drivers
            query = db.query(Driver).filter(Driver.status != "Deactivated")
            if available_only:
                query = query.filter(Driver.status == "Available")
            if min_hos_remaining:
                query = query.filter(Driver.hours_of_service_remaining >= min_hos_remaining)

            drivers = query.order_by(Driver.name.asc()).all()
            results = []
            for d in drivers:
                v = db.query(Vehicle).filter(Vehicle.id == d.current_vehicle_id).first() if d.current_vehicle_id else None
                act_count = db.query(Shipment).filter(
                    Shipment.driver_id == d.id,
                    Shipment.status.in_(["Assigned", "Picked Up", "In Transit", "Delayed"])
                ).count()
                
                if active_only and act_count == 0:
                    continue
                    
                results.append({
                    "driver_code": d.driver_code,
                    "name": d.name,
                    "phone": d.phone,
                    "status": d.status,
                    "rating": d.rating,
                    "license_type": d.license_type,
                    "hours_of_service_remaining": d.hours_of_service_remaining,
                    "assigned_vehicle": v.vehicle_code if v else "None",
                    "active_shipments_count": act_count
                })

            return {
                "count": len(results),
                "drivers": results
            }

        finally:
            db.close()

driver_management_tool = DriverManagementTool()
