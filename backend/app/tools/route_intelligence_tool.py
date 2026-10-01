from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from app.tools.base import BaseAgentTool
from app.core.database import SessionLocal
from app.models.route import Route
from app.models.shipment import Shipment
from app.services.cost_service import cost_service
from app.tools.route_optimization_tool import route_optimization_tool

class RouteIntelligenceTool(BaseAgentTool):
    name: str = "route_intelligence_tool"
    description: str = (
        "Perform deep route intelligence, compare active corridor against recommended bypasses, "
        "analyze toll vs distance trade-offs, and compute efficiency and risk for routes or shipments."
    )
    allowed_roles: List[str] = ["Admin", "Logistics Manager", "Dispatcher", "Driver", "Operations Team", "Analyst"]
    required_permissions: List[str] = ["routes:read"]
    data_scope: str = "routes"

    def execute(
        self,
        route_code: Optional[str] = None,
        shipment_code: Optional[str] = None,
        compare_alternatives: bool = True,
        user_context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        
        is_auth, err = self.check_authorization(user_context)
        if not is_auth:
            return {"success": False, "error": err}

        db: Session = SessionLocal()
        try:
            r = None
            if route_code:
                r = db.query(Route).filter(Route.route_code == route_code.strip().upper()).first()
                if not r:
                    return {
                        "success": False,
                        "error": f"Route '{route_code}' not found."
                    }
            elif shipment_code:
                shp = db.query(Shipment).filter(Shipment.shipment_code == shipment_code.strip().upper()).first()
                if shp:
                    r = db.query(Route).filter(Route.shipment_id == shp.id).first()
                if not r:
                    return {
                        "success": False,
                        "error": f"Route for shipment '{shipment_code}' not found."
                    }
            else:
                # Return network route performance summary
                routes = db.query(Route).all()
                total_dist = sum(x.planned_distance_km or 0.0 for x in routes)
                avg_dist = round(total_dist / len(routes), 1) if routes else 0.0
                return {
                    "success": True,
                    "total_network_routes": len(routes),
                    "average_distance_km": avg_dist,
                    "active_corridors": len([x for x in routes if x.status == "In Transit"])
                }

            # Run route optimization tool calculation
            opt_res = route_optimization_tool.execute(
                shipment_code=shipment_code or (f"SHP-R{r.shipment_id}" if r and r.shipment_id else None),
                origin_id=r.origin_id if r else None,
                destination_id=r.destination_id if r else None,
                priority="fastest",
                user_context=user_context
            )

            primary = opt_res.get("recommended_route", {})
            alt = opt_res.get("alternative_route", {})
            
            p_dist = primary.get("distance_km", r.planned_distance_km if r else 500.0)
            a_dist = alt.get("distance_km", p_dist * 1.08)

            cost_comparison = cost_service.compare_route_costs(
                primary_distance_km=p_dist,
                alternative_distance_km=a_dist,
                primary_toll_fees=25.0,
                alternative_toll_fees=0.0
            )

            return {
                "success": True,
                "route_code": r.route_code if r else route_code or "N/A",
                "status": (r.status if r and r.status else "Planned"),
                "primary_corridor": primary,
                "alternative_corridor": alt,
                "cost_comparison": cost_comparison,
                "optimization_summary": opt_res.get("explanation")
            }
        finally:
            db.close()

route_intelligence_tool = RouteIntelligenceTool()
