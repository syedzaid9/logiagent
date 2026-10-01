from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from app.tools.base import BaseAgentTool
from app.core.database import SessionLocal
from app.models.vehicle import Vehicle
from app.models.driver import Driver

class VehicleAvailabilityTool(BaseAgentTool):
    name: str = "vehicle_availability_tool"
    description: str = (
        "Find available vehicles matching weight capacity (e.g. 1500 kg), check specific vehicle status, "
        "inspect vehicle locations, or compute overall fleet capacity availability."
    )
    allowed_roles = ["Admin", "Logistics Manager", "Dispatcher", "Driver", "Operations Team"]
    data_scope = "vehicles"

    def execute(
        self,
        min_capacity_kg: Optional[float] = None,
        vehicle_type: Optional[str] = None,
        vehicle_code: Optional[str] = None,
        status: Optional[str] = None,
        user_context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        
        is_auth, err = self.check_authorization(user_context)
        if not is_auth:
            return {"found": False, "error": err}

        role = user_context.get("role") if user_context else None
        driver_id = user_context.get("driver_id") if user_context else None
        from app.tools.base import normalize_role
        norm_role = normalize_role(role)

        db: Session = SessionLocal()
        try:
            # Driver Scope Verification
            if norm_role == "DRIVER":
                if not driver_id:
                    email = user_context.get("email") if user_context else None
                    if email:
                        d_rec = db.query(Driver).filter(Driver.email == email).first()
                        if d_rec:
                            driver_id = d_rec.id

                if not driver_id:
                    return {"success": False, "found": False, "error": "Your driver account is not linked to an active driver profile."}
                
                driver = db.query(Driver).filter(Driver.id == driver_id).first()
                if not driver or not driver.current_vehicle_id:
                    return {"success": False, "found": False, "error": "No vehicle is currently assigned to your driver profile."}

                assigned_veh = db.query(Vehicle).filter(Vehicle.id == driver.current_vehicle_id).first()
                if not assigned_veh:
                    return {"success": False, "found": False, "error": "Assigned vehicle record not found."}

                # If asking for a specific vehicle code, verify it is their assigned vehicle
                if vehicle_code:
                    v_clean = vehicle_code.strip().upper()
                    if assigned_veh.vehicle_code.upper() != v_clean and v_clean not in assigned_veh.vehicle_code.upper():
                        return {
                            "success": False,
                            "found": False,
                            "error": f"Access denied. Vehicle '{vehicle_code}' is not assigned to you. Drivers can only inspect their own assigned vehicle ({assigned_veh.vehicle_code})."
                        }

                # If asking for general fleet availability, block and return only own assigned vehicle
                remaining_cap = max(0.0, assigned_veh.max_capacity_kg - assigned_veh.current_load_kg)
                utilization = round((assigned_veh.current_load_kg / assigned_veh.max_capacity_kg) * 100.0, 1) if assigned_veh.max_capacity_kg > 0 else 0.0

                return {
                    "success": True,
                    "found": True,
                    "is_assigned_vehicle": True,
                    "assigned_vehicle": {
                        "vehicle_code": assigned_veh.vehicle_code,
                        "model": assigned_veh.model,
                        "type": assigned_veh.type,
                        "status": assigned_veh.status,
                        "max_capacity_kg": assigned_veh.max_capacity_kg,
                        "current_load_kg": assigned_veh.current_load_kg,
                        "remaining_capacity_kg": remaining_cap,
                        "utilization_pct": utilization,
                        "fuel_level_pct": assigned_veh.fuel_level_pct,
                        "current_location": assigned_veh.current_location,
                    },
                    "vehicle_code": assigned_veh.vehicle_code,
                    "model": assigned_veh.model,
                    "type": assigned_veh.type,
                    "status": assigned_veh.status,
                    "max_capacity_kg": assigned_veh.max_capacity_kg,
                    "current_load_kg": assigned_veh.current_load_kg,
                    "remaining_capacity_kg": remaining_cap,
                    "utilization_pct": utilization,
                    "fuel_level_pct": assigned_veh.fuel_level_pct,
                    "current_location": assigned_veh.current_location,
                    "message": f"Your assigned operational vehicle is {assigned_veh.vehicle_code} ({assigned_veh.model}). Fleet-wide inventory browsing is restricted to Dispatchers and Management."
                }

            # Dispatcher, Manager, Admin fleet search
            if vehicle_code:
                v_clean = vehicle_code.strip().upper()
                vehicle = db.query(Vehicle).filter(Vehicle.vehicle_code == v_clean).first()
                if not vehicle:
                    vehicle = db.query(Vehicle).filter(Vehicle.vehicle_code.like(f"%{v_clean}%")).first()

                if not vehicle:
                    return {"success": False, "found": False, "error": f"Vehicle '{vehicle_code}' not found."}

                driver = db.query(Driver).filter(Driver.id == vehicle.driver_id).first() if vehicle.driver_id else None
                remaining_cap = max(0.0, vehicle.max_capacity_kg - vehicle.current_load_kg)
                utilization = round((vehicle.current_load_kg / vehicle.max_capacity_kg) * 100.0, 1)

                return {
                    "success": True,
                    "found": True,
                    "vehicle_code": vehicle.vehicle_code,
                    "model": vehicle.model,
                    "type": vehicle.type,
                    "status": vehicle.status,
                    "max_capacity_kg": vehicle.max_capacity_kg,
                    "current_load_kg": vehicle.current_load_kg,
                    "remaining_capacity_kg": remaining_cap,
                    "utilization_pct": utilization,
                    "fuel_level_pct": vehicle.fuel_level_pct,
                    "fuel_type": vehicle.fuel_type,
                    "current_location": vehicle.current_location,
                    "coordinates": {"latitude": vehicle.latitude, "longitude": vehicle.longitude},
                    "driver_assigned": driver.name if driver else "None"
                }

            # Query available vehicles
            query = db.query(Vehicle)
            if status:
                query = query.filter(Vehicle.status.ilike(f"%{status}%"))
            else:
                # Default to Available
                query = query.filter(Vehicle.status == "Available")

            if vehicle_type:
                query = query.filter(Vehicle.type.ilike(f"%{vehicle_type}%"))

            vehicles = query.all()

            suitable = []
            for v in vehicles:
                remaining_cap = max(0.0, v.max_capacity_kg - v.current_load_kg)
                if min_capacity_kg is not None and remaining_cap < min_capacity_kg:
                    continue

                driver = db.query(Driver).filter(Driver.id == v.driver_id).first() if v.driver_id else None
                suitable.append({
                    "vehicle_code": v.vehicle_code,
                    "model": v.model,
                    "type": v.type,
                    "status": v.status,
                    "max_capacity_kg": v.max_capacity_kg,
                    "current_load_kg": v.current_load_kg,
                    "available_capacity_kg": remaining_cap,
                    "fuel_level_pct": v.fuel_level_pct,
                    "current_location": v.current_location,
                    "driver": driver.name if driver else "Ready for assignment"
                })

            # Sort by best fit capacity
            suitable.sort(key=lambda x: x["available_capacity_kg"])

            total_fleet = db.query(Vehicle).count()

            return {
                "success": True,
                "available_count": len(suitable),
                "available_vehicles_count": len(suitable),
                "total_fleet_count": total_fleet,
                "requested_min_capacity_kg": min_capacity_kg,
                "vehicles": suitable
            }

        finally:
            db.close()

vehicle_availability_tool = VehicleAvailabilityTool()
