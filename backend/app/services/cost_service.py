from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.shipment import Shipment
from app.models.route import Route
from app.models.vehicle import Vehicle
from app.models.cost import TransportationCost
from app.ml.cost_optimizer import cost_optimizer

class CostService:
    """
    Unified Transportation Cost & Pricing Intelligence Service.
    Maintains exact parity across DB records, route optimizations, and ML cost estimations.
    """

    def estimate_shipment_cost(self, db: Session, identifier: str | int) -> Dict[str, Any]:
        """Calculates or retrieves authoritative transportation cost for a shipment."""
        shp = None
        if isinstance(identifier, int) or (isinstance(identifier, str) and identifier.isdigit()):
            shp = db.query(Shipment).filter(Shipment.id == int(identifier)).first()
        else:
            clean_code = str(identifier).strip().upper()
            shp = db.query(Shipment).filter(Shipment.shipment_code == clean_code).first()

        if not shp:
            return {
                "success": False,
                "error": f"Shipment '{identifier}' not found in database."
            }

        # Check existing persisted cost record
        cost_rec = db.query(TransportationCost).filter(TransportationCost.shipment_id == shp.id).first()
        route = db.query(Route).filter(Route.shipment_id == shp.id).first()
        vehicle = db.query(Vehicle).filter(Vehicle.id == shp.vehicle_id).first() if shp.vehicle_id else None

        distance_km = route.planned_distance_km if route and route.planned_distance_km else (cost_rec.distance_km if cost_rec else 450.0)
        v_type = vehicle.type if vehicle else "Semi-Truck (Dry Van)"

        ml_cost = cost_optimizer.calculate_trip_cost(distance_km=distance_km, vehicle_type=v_type)

        return {
            "success": True,
            "shipment_code": shp.shipment_code,
            "distance_km": distance_km,
            "vehicle_type": v_type,
            "total_cost_usd": cost_rec.total_cost if cost_rec else ml_cost["total_cost"],
            "cost_per_km": round((cost_rec.total_cost / distance_km), 2) if cost_rec and distance_km > 0 else ml_cost["cost_per_km"],
            "cost_breakdown": {
                "fuel_cost": cost_rec.fuel_cost if cost_rec else ml_cost["fuel_cost"],
                "driver_cost": cost_rec.driver_wage_cost if cost_rec else ml_cost["driver_cost"],
                "toll_cost": cost_rec.toll_cost if cost_rec else ml_cost["toll_cost"],
                "maintenance_cost": cost_rec.maintenance_cost if cost_rec else ml_cost["maintenance_cost"]
            },
            "is_persisted": cost_rec is not None
        }

    def estimate_route_cost(
        self,
        distance_km: float,
        vehicle_type: str = "Semi-Truck (Dry Van)",
        toll_fees: float = 25.0
    ) -> Dict[str, Any]:
        """Estimates transportation cost for a planned route distance."""
        res = cost_optimizer.calculate_trip_cost(
            distance_km=distance_km,
            vehicle_type=vehicle_type,
            toll_fees=toll_fees
        )
        return {
            "success": True,
            **res
        }

    def compare_route_costs(
        self,
        primary_distance_km: float,
        alternative_distance_km: float,
        vehicle_type: str = "Semi-Truck (Dry Van)",
        primary_toll_fees: float = 25.0,
        alternative_toll_fees: float = 0.0
    ) -> Dict[str, Any]:
        """Compares operational costs between two routing corridors."""
        c1 = cost_optimizer.calculate_trip_cost(primary_distance_km, vehicle_type=vehicle_type, toll_fees=primary_toll_fees)
        c2 = cost_optimizer.calculate_trip_cost(alternative_distance_km, vehicle_type=vehicle_type, toll_fees=alternative_toll_fees)

        cost_diff = round(c2["total_cost"] - c1["total_cost"], 2)
        dist_diff = round(alternative_distance_km - primary_distance_km, 1)

        recommendation = (
            "Primary corridor is cost optimal." if cost_diff >= 0
            else f"Alternative bypass saves ${abs(cost_diff):.2f} USD."
        )

        return {
            "success": True,
            "primary_corridor": {
                "distance_km": primary_distance_km,
                "total_cost": c1["total_cost"],
                "toll_fees": primary_toll_fees,
                "cost_per_km": c1["cost_per_km"]
            },
            "alternative_corridor": {
                "distance_km": alternative_distance_km,
                "total_cost": c2["total_cost"],
                "toll_fees": alternative_toll_fees,
                "cost_per_km": c2["cost_per_km"]
            },
            "cost_difference_usd": cost_diff,
            "distance_difference_km": dist_diff,
            "recommendation": recommendation
        }

cost_service = CostService()
