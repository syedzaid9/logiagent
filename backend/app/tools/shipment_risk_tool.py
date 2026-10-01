from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from app.tools.base import BaseAgentTool
from app.core.database import SessionLocal
from app.services.shipment_risk_service import shipment_risk_service

class ShipmentRiskTool(BaseAgentTool):
    name: str = "shipment_risk_tool"
    description: str = (
        "Evaluate comprehensive shipment risk score (0-100), predict delay probability, "
        "estimate arrival ETA against delivery deadlines, identify root-cause risk factors, "
        "and generate operational mitigation recommendations for any shipment code (e.g. SHP-1001)."
    )
    allowed_roles: List[str] = ["Admin", "Logistics Manager", "Dispatcher", "Driver", "Operations Team", "Analyst"]
    required_permissions: List[str] = ["shipments:read"]
    data_scope: str = "shipments"

    def execute(
        self,
        shipment_code: Optional[str] = None,
        network_summary: bool = False,
        user_context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        
        is_auth, err = self.check_authorization(user_context)
        if not is_auth:
            return {"success": False, "error": err}

        db: Session = SessionLocal()
        try:
            if network_summary or not shipment_code:
                return {
                    "success": True,
                    **shipment_risk_service.get_network_risk_summary(db=db, user_context=user_context)
                }

            res = shipment_risk_service.analyze_shipment_risk(
                db=db,
                identifier=shipment_code,
                user_context=user_context
            )
            return {
                "success": res.get("prediction_status") == "success",
                **res
            }
        finally:
            db.close()

shipment_risk_tool = ShipmentRiskTool()
