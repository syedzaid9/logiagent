import math
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from app.tools.base import BaseAgentTool
from app.core.database import SessionLocal
from app.models.route import Route
from app.models.shipment import Shipment
from app.models.location import DeliveryLocation
from app.models.vehicle import Vehicle
from app.ml.cost_optimizer import cost_optimizer

class RouteOptimizationTool(BaseAgentTool):
    name: str = "route_optimization_tool"
    description: str = (
        "Calculate the fastest or lowest-cost route between logistics hubs or for a specific shipment (e.g. SHP-1001), "
        "comparing highway corridors, traffic congestion, distance, duration, and estimated transportation cost."
    )
    allowed_roles: List[str] = ["ADMIN", "LOGISTICS_MANAGER", "DISPATCHER", "DRIVER"]
    required_permissions: List[str] = ["routes:read"]
    data_scope: str = "Scoped to driver's assigned shipments or dispatcher/manager network corridors"

    def _haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        R = 6371.0 # Earth radius in km
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    def execute(
        self,
        shipment_code: Optional[str] = None,
        route_code: Optional[str] = None,
        origin_id: Optional[int] = None,
        destination_id: Optional[int] = None,
        priority: str = "fastest", # fastest, shortest, lowest_cost
        user_context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        
        ctx = user_context or getattr(self, "user_context", None) or {}
        user_role = (ctx.get("role") or "").upper().replace(" ", "_")
        driver_id = ctx.get("driver_id")

        db: Session = SessionLocal()
        try:
            shipment = None
            db_route = None

            # Driver-specific scoping: resolve driver's assigned shipment if not provided
            if user_role == "DRIVER":
                if not driver_id:
                    from app.models.driver import Driver
                    email = ctx.get("email")
                    if email:
                        d = db.query(Driver).filter(Driver.email == email).first()
                        if d:
                            driver_id = d.id

                if not shipment_code and not route_code:
                    # Auto-bind driver's active shipment
                    if driver_id:
                        shipment = db.query(Shipment).filter(
                            Shipment.driver_id == driver_id,
                            Shipment.status.in_(["In Transit", "Delayed", "Pending", "Dispatched"])
                        ).first()
                        if not shipment:
                            shipment = db.query(Shipment).filter(Shipment.driver_id == driver_id).first()

            if route_code:
                rc_clean = route_code.strip().upper()
                db_route = db.query(Route).filter(Route.route_code == rc_clean).first()
                if not db_route:
                    db_route = db.query(Route).filter(Route.route_code.like(f"%{rc_clean}%")).first()
                if db_route:
                    origin_id = db_route.origin_id
                    destination_id = db_route.destination_id
                    if db_route.shipment_id:
                        shipment = db.query(Shipment).filter(Shipment.id == db_route.shipment_id).first()
                else:
                    return {"success": False, "error": f"Route '{route_code}' not found."}

            if shipment_code and not db_route:
                code_clean = shipment_code.strip().upper()
                shipment = db.query(Shipment).filter(Shipment.shipment_code == code_clean).first()
                if not shipment:
                    shipment = db.query(Shipment).filter(Shipment.shipment_code.like(f"%{code_clean}%")).first()

                if shipment:
                    origin_id = shipment.origin_id
                    destination_id = shipment.destination_id
                    db_route = db.query(Route).filter(Route.shipment_id == shipment.id).first()
                else:
                    return {"success": False, "error": f"Shipment '{shipment_code}' not found."}

            # Security check for Drivers: cannot access or optimize other drivers' shipments
            if user_role == "DRIVER" and shipment:
                if driver_id and shipment.driver_id and shipment.driver_id != driver_id:
                    return {
                        "success": False,
                        "error": "Unauthorized: You are only permitted to optimize routes for your own assigned shipments."
                    }

            if not origin_id or not destination_id:
                if user_role == "DRIVER":
                    return {
                        "success": False,
                        "error": "No assigned route found for your account. Please provide an assigned shipment code."
                    }
                # Default to central hub route if unspecified for manager/dispatcher
                orig = db.query(DeliveryLocation).first()
                dest = db.query(DeliveryLocation).offset(1).first()
                if orig and dest:
                    origin_id = orig.id
                    destination_id = dest.id
                else:
                    return {"success": False, "error": "Origin and destination required."}

            origin = db.query(DeliveryLocation).filter(DeliveryLocation.id == origin_id).first()
            destination = db.query(DeliveryLocation).filter(DeliveryLocation.id == destination_id).first()

            if not origin or not destination:
                return {"success": False, "error": "Specified locations not found in database."}

            # Check if pre-computed route exists in DB if not found yet
            if not db_route:
                db_route = db.query(Route).filter(
                    Route.origin_id == origin_id,
                    Route.destination_id == destination_id
                ).first()

            if not db_route:
                geo_dist = self._haversine_distance(origin.latitude, origin.longitude, destination.latitude, destination.longitude)
                distance_km = round(max(50.0, geo_dist * 1.25), 1)
                duration_min = int((distance_km / 70.0) * 60)
                traffic = "Moderate"
                weather = "Clear"
                route_code_val = "RT-AUTO"
                status_val = "Planned"
            else:
                distance_km = db_route.planned_distance_km
                duration_min = db_route.planned_duration_min
                traffic = db_route.traffic_condition or "Moderate"
                weather = db_route.weather_condition or "Clear"
                route_code_val = db_route.route_code
                status_val = db_route.status or "Planned"

            fastest_duration = int(duration_min * (1.15 if traffic == "Heavy" else 1.0))
            fastest_distance = distance_km
            
            toll_free_distance = round(distance_km * 1.08, 1)
            toll_free_duration = int(duration_min * 1.22)
            
            cost_details = cost_optimizer.calculate_trip_cost(distance_km=distance_km)

            mid_lat = (origin.latitude + destination.latitude) / 2
            mid_lng = (origin.longitude + destination.longitude) / 2
            
            waypoints = [
                {"name": f"Origin: {origin.name}", "location": f"{origin.city}, {origin.state}", "lat": origin.latitude, "lng": origin.longitude, "type": "Origin"},
                {"name": "Midway Logistics Fuel Depot", "location": "Interstate Rest & Inspection Station", "lat": round(mid_lat, 4), "lng": round(mid_lng, 4), "type": "Fuel & Rest"},
                {"name": f"Destination: {destination.name}", "location": f"{destination.city}, {destination.state}", "lat": destination.latitude, "lng": destination.longitude, "type": "Destination"}
            ]

            polyline = [
                [origin.latitude, origin.longitude],
                [round(mid_lat + 0.15, 4), round(mid_lng - 0.20, 4)],
                [round(mid_lat, 4), round(mid_lng, 4)],
                [round(mid_lat - 0.10, 4), round(mid_lng + 0.15, 4)],
                [destination.latitude, destination.longitude]
            ]

            # Cost details hidden from drivers
            cost_usd = None if user_role == "DRIVER" else cost_details["total_cost"]

            recommendation = (
                f"Recommended Route: Primary Corridor via I-90/I-80 Express. "
                f"Distance: {fastest_distance} km, Estimated Travel Time: {fastest_duration // 60}h {fastest_duration % 60}m. "
                f"Traffic condition is {traffic}."
            )
            if cost_usd is not None:
                recommendation += f" Total estimated cost: ${cost_usd} USD."

            resp = {
                "success": True,
                "route_code": route_code_val,
                "status": status_val,
                "shipment_code": shipment.shipment_code if shipment else None,
                "origin": f"{origin.name} ({origin.city}, {origin.state})",
                "destination": f"{destination.name} ({destination.city}, {destination.state})",
                "recommended_priority": priority,
                "recommended_route": {
                    "corridor": "Interstate Express Corridor",
                    "distance_km": fastest_distance,
                    "duration_minutes": fastest_duration,
                    "duration_formatted": f"{fastest_duration // 60}h {fastest_duration % 60}m",
                    "traffic_condition": traffic,
                    "weather_condition": weather,
                },
                "alternative_routes": [
                    {
                        "corridor": "State Highway Bypass (Toll-Free)",
                        "distance_km": toll_free_distance,
                        "duration_minutes": toll_free_duration,
                        "duration_formatted": f"{toll_free_duration // 60}h {toll_free_duration % 60}m",
                        "traffic_condition": "Light",
                    }
                ],
                "stops": waypoints,
                "polyline_coordinates": polyline,
                "recommendation_summary": recommendation
            }

            if cost_usd is not None:
                resp["recommended_route"]["estimated_cost_usd"] = cost_usd
                resp["recommended_route"]["cost_per_km"] = cost_details["cost_per_km"]
                resp["alternative_routes"][0]["estimated_cost_usd"] = round(cost_usd * 0.92, 2)

            return resp

        finally:
            db.close()

route_optimization_tool = RouteOptimizationTool()

