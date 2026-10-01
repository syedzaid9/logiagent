from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from app.tools.base import BaseAgentTool
from app.core.database import SessionLocal
from app.services.anomaly_detection_service import anomaly_detection_service
from app.services.recommendation_service import recommendation_service

class AnomalyAlertsTool(BaseAgentTool):
    name: str = "anomaly_alerts_tool"
    description: str = (
        "Scan operational state for anomalies (severe delays, driver HOS issues, underutilized fleet, "
        "cost anomalies), retrieve active operational alerts, and view AI recommendations."
    )
    allowed_roles: List[str] = ["Admin", "Logistics Manager", "Dispatcher", "Operations Team", "Analyst"]
    required_permissions: List[str] = ["analytics:read"]
    data_scope: str = "alerts"

    def execute(
        self,
        scan_now: bool = False,
        status: Optional[str] = "active",
        severity: Optional[str] = None,
        include_recommendations: bool = True,
        user_context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        
        is_auth, err = self.check_authorization(user_context)
        if not is_auth:
            return {"success": False, "error": err}

        db: Session = SessionLocal()
        try:
            if scan_now:
                anomaly_detection_service.scan_and_generate_alerts(db)

            alerts = anomaly_detection_service.list_alerts(
                db=db,
                status=status,
                severity=severity,
                limit=15
            )

            recs = []
            if include_recommendations:
                recs = recommendation_service.generate_recommendations(db=db, user_context=user_context, limit=5)

            summary = anomaly_detection_service.get_alerts_summary(db)

            return {
                "success": True,
                "alerts_summary": summary,
                "active_alerts_count": len(alerts),
                "alerts": [a.to_dict() for a in alerts],
                "ai_recommendations": recs
            }
        finally:
            db.close()

anomaly_alerts_tool = AnomalyAlertsTool()
