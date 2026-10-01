from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from sqlalchemy import func
from app.tools.base import BaseAgentTool
from app.core.database import SessionLocal
from app.models.cost import TransportationCost
from app.models.shipment import Shipment
from app.models.vehicle import Vehicle
from app.models.route import Route
from app.ml.cost_optimizer import cost_optimizer

class CostCalculationTool(BaseAgentTool):
    name: str = "cost_calculation_tool"
    description: str = (
        "Calculate transportation costs, fuel expenses, cost per kilometer, toll fees, "
        "and total operational expenditure for specific shipments or fleet-wide monthly spend."
    )
    allowed_roles = ["Admin", "Logistics Manager", "Operations Team"]
    data_scope = "financial"

    def execute(
        self,
        shipment_code: Optional[str] = None,
        distance_km: Optional[float] = None,
        vehicle_type: Optional[str] = None,
        fleet_monthly_total: bool = False,
        user_context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        
        is_auth, err = self.check_authorization(user_context)
        if not is_auth:
            return {"success": False, "error": err}

        db: Session = SessionLocal()
        try:
            if fleet_monthly_total or (not shipment_code and not distance_km):
                # Calculate aggregated fleet costs
                total_cost_sum = db.query(func.sum(TransportationCost.total_cost)).scalar() or 0.0
                fuel_cost_sum = db.query(func.sum(TransportationCost.fuel_cost)).scalar() or 0.0
                driver_wage_sum = db.query(func.sum(TransportationCost.driver_wage_cost)).scalar() or 0.0
                toll_cost_sum = db.query(func.sum(TransportationCost.toll_cost)).scalar() or 0.0
                maintenance_sum = db.query(func.sum(TransportationCost.maintenance_cost)).scalar() or 0.0
                total_distance_sum = db.query(func.sum(TransportationCost.distance_km)).scalar() or 1.0

                avg_cost_per_km = round(total_cost_sum / total_distance_sum, 2) if total_distance_sum > 0 else 2.15

                return {
                    "success": True,
                    "period": "Current Month",
                    "total_transportation_cost_usd": round(total_cost_sum, 2),
                    "total_fleet_distance_km": round(total_distance_sum, 1),
                    "average_cost_per_km_usd": avg_cost_per_km,
                    "cost_breakdown": {
                        "fuel_cost_usd": round(fuel_cost_sum, 2),
                        "driver_labor_usd": round(driver_wage_sum, 2),
                        "tolls_usd": round(toll_cost_sum, 2),
                        "maintenance_depreciation_usd": round(maintenance_sum, 2)
                    },
                    "currency": "USD"
                }

            if shipment_code:
                code_clean = shipment_code.strip().upper()
                shipment = db.query(Shipment).filter(Shipment.shipment_code == code_clean).first()
                if not shipment:
                    shipment = db.query(Shipment).filter(Shipment.shipment_code.like(f"%{code_clean}%")).first()

                if not shipment:
                    return {"success": False, "error": f"Shipment '{shipment_code}' not found."}

                cost_record = db.query(TransportationCost).filter(TransportationCost.shipment_id == shipment.id).first()
                vehicle = db.query(Vehicle).filter(Vehicle.id == shipment.vehicle_id).first() if shipment.vehicle_id else None
                route = db.query(Route).filter(Route.shipment_id == shipment.id).first()
                if not route and shipment.origin_id and shipment.destination_id:
                    route = db.query(Route).filter(
                        Route.origin_id == shipment.origin_id,
                        Route.destination_id == shipment.destination_id
                    ).first()
                
                v_type = vehicle.type if vehicle else (vehicle_type or "Semi-Truck (Dry Van)")
                if cost_record:
                    dist = cost_record.distance_km
                elif route and route.planned_distance_km:
                    dist = route.planned_distance_km
                else:
                    from app.services.maps_service import maps_service
                    from app.models.location import DeliveryLocation
                    orig = db.query(DeliveryLocation).filter(DeliveryLocation.id == shipment.origin_id).first()
                    dest = db.query(DeliveryLocation).filter(DeliveryLocation.id == shipment.destination_id).first()
                    if orig and dest:
                        calc = maps_service.calculate_distance_and_duration(orig.latitude, orig.longitude, dest.latitude, dest.longitude)
                        dist = calc.get("distance_km", 450.0)
                    else:
                        dist = 450.0

                if cost_record:
                    return {
                        "success": True,
                        "shipment_code": shipment.shipment_code,
                        "vehicle_type": v_type,
                        "distance_km": cost_record.distance_km,
                        "fuel_cost": cost_record.fuel_cost,
                        "driver_cost": cost_record.driver_wage_cost,
                        "toll_cost": cost_record.toll_cost,
                        "maintenance_cost": cost_record.maintenance_cost,
                        "total_cost_usd": cost_record.total_cost,
                        "cost_per_km": cost_record.cost_per_km,
                        "currency": "USD"
                    }
                else:
                    calculated = cost_optimizer.calculate_trip_cost(distance_km=dist, vehicle_type=v_type)
                    return {
                        "success": True,
                        "shipment_code": shipment.shipment_code,
                        **calculated
                    }

            # Custom distance calculation
            if distance_km:
                v_type = vehicle_type or "Semi-Truck (Dry Van)"
                calculated = cost_optimizer.calculate_trip_cost(distance_km=distance_km, vehicle_type=v_type)
                return {
                    "success": True,
                    **calculated
                }

            return {"success": False, "error": "Insufficient parameters."}

        finally:
            db.close()

cost_calculation_tool = CostCalculationTool()
