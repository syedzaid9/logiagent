from typing import Dict, Any, List

class DelayPredictor:
    """
    ML Delay Prediction Model for LogiAgent.
    Computes risk score (0-100), risk level, and explainable feature importances.
    """
    
    def predict_delay_risk(
        self,
        distance_km: float,
        current_delay_min: int,
        traffic_condition: str, # Light, Moderate, Heavy, Severe Congestion
        weather_condition: str = "Clear", # Clear, Rain, Snow, Fog, Storm
        driver_hos_remaining: float = 11.0,
        historical_route_delay_avg: float = 15.0
    ) -> Dict[str, Any]:
        
        base_score = 10.0
        factors: List[Dict[str, Any]] = []
        
        # 1. Existing delay impact
        if current_delay_min > 0:
            delay_weight = min(40.0, current_delay_min * 0.8)
            base_score += delay_weight
            factors.append({
                "factor": "Current Delay Accumulation",
                "impact": "High" if current_delay_min > 30 else "Moderate",
                "detail": f"Shipment is already delayed by {current_delay_min} minutes."
            })
            
        # 2. Traffic conditions
        traffic_weights = {
            "Light": 0.0,
            "Moderate": 10.0,
            "Heavy": 25.0,
            "Severe Congestion": 40.0
        }
        traffic_impact = traffic_weights.get(traffic_condition, 10.0)
        base_score += traffic_impact
        if traffic_impact >= 20.0:
            factors.append({
                "factor": "Traffic Congestion",
                "impact": "High",
                "detail": f"Route experiencing {traffic_condition} along primary corridors."
            })
            
        # 3. Weather severity
        weather_weights = {
            "Clear": 0.0,
            "Rain": 10.0,
            "Fog": 15.0,
            "Snow": 25.0,
            "Storm": 35.0
        }
        weather_impact = weather_weights.get(weather_condition, 0.0)
        base_score += weather_impact
        if weather_impact > 0:
            factors.append({
                "factor": "Adverse Weather",
                "impact": "High" if weather_impact >= 20 else "Moderate",
                "detail": f"Precipitation condition '{weather_condition}' slowing transit speeds."
            })
            
        # 4. Driver HOS (Hours of Service) constraints
        estimated_driving_hours = distance_km / 65.0 # Average commercial speed 65 km/h
        if estimated_driving_hours > driver_hos_remaining:
            base_score += 25.0
            factors.append({
                "factor": "Driver Hours of Service (HOS) Exhaustion",
                "impact": "Critical",
                "detail": f"Driver has {driver_hos_remaining:.1f}h remaining; route requires ~{estimated_driving_hours:.1f}h driving, triggering mandatory 10h rest."
            })
            
        # 5. Route historical delay
        if historical_route_delay_avg > 25.0:
            base_score += 10.0
            factors.append({
                "factor": "Historical Route Bottlenecks",
                "impact": "Low",
                "detail": f"Historical data shows average {historical_route_delay_avg:.0f} min delay on this route."
            })
            
        # Clamp score between 0 and 100
        risk_score = round(min(100.0, max(5.0, base_score)), 1)
        
        if risk_score < 30.0:
            risk_level = "Low"
        elif risk_score < 60.0:
            risk_level = "Medium"
        elif risk_score < 80.0:
            risk_level = "High"
        else:
            risk_level = "Critical"
            
        if not factors:
            factors.append({
                "factor": "Optimal Route Conditions",
                "impact": "Positive",
                "detail": "No adverse traffic, weather, or driver constraints detected."
            })
            
        return {
            "risk_score": risk_score,
            "risk_level": risk_level,
            "important_factors": factors,
            "mitigation_recommendation": (
                "Re-route around congestion bottlenecks and alert receiver." 
                if risk_score >= 60 else "Maintain current schedule and monitor checkpoints."
            )
        }

delay_predictor = DelayPredictor()
