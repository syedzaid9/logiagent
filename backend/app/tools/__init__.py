from app.tools.base import BaseAgentTool
from app.tools.shipment_tracking_tool import shipment_tracking_tool, ShipmentTrackingTool
from app.tools.vehicle_availability_tool import vehicle_availability_tool, VehicleAvailabilityTool
from app.tools.driver_management_tool import driver_management_tool, DriverManagementTool
from app.tools.route_optimization_tool import route_optimization_tool, RouteOptimizationTool
from app.tools.eta_calculation_tool import eta_calculation_tool, ETACalculationTool
from app.tools.delay_detection_tool import delay_detection_tool, DelayDetectionTool
from app.tools.cost_calculation_tool import cost_calculation_tool, CostCalculationTool
from app.tools.logistics_analytics_tool import logistics_analytics_tool, LogisticsAnalyticsTool
from app.tools.notification_tool import notification_tool, NotificationTool
from app.tools.shipment_risk_tool import shipment_risk_tool, ShipmentRiskTool
from app.tools.route_intelligence_tool import route_intelligence_tool, RouteIntelligenceTool
from app.tools.anomaly_alerts_tool import anomaly_alerts_tool, AnomalyAlertsTool

TOOLS_REGISTRY = {
    "shipment_tracking_tool": shipment_tracking_tool,
    "vehicle_availability_tool": vehicle_availability_tool,
    "driver_management_tool": driver_management_tool,
    "route_optimization_tool": route_optimization_tool,
    "eta_calculation_tool": eta_calculation_tool,
    "delay_detection_tool": delay_detection_tool,
    "cost_calculation_tool": cost_calculation_tool,
    "logistics_analytics_tool": logistics_analytics_tool,
    "notification_tool": notification_tool,
    "shipment_risk_tool": shipment_risk_tool,
    "route_intelligence_tool": route_intelligence_tool,
    "anomaly_alerts_tool": anomaly_alerts_tool,
}

__all__ = [
    "BaseAgentTool",
    "TOOLS_REGISTRY",
    "shipment_tracking_tool",
    "ShipmentTrackingTool",
    "vehicle_availability_tool",
    "VehicleAvailabilityTool",
    "driver_management_tool",
    "DriverManagementTool",
    "route_optimization_tool",
    "RouteOptimizationTool",
    "eta_calculation_tool",
    "ETACalculationTool",
    "delay_detection_tool",
    "DelayDetectionTool",
    "cost_calculation_tool",
    "CostCalculationTool",
    "logistics_analytics_tool",
    "LogisticsAnalyticsTool",
    "notification_tool",
    "NotificationTool",
    "shipment_risk_tool",
    "ShipmentRiskTool",
    "route_intelligence_tool",
    "RouteIntelligenceTool",
    "anomaly_alerts_tool",
    "AnomalyAlertsTool",
]
