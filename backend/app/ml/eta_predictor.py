from datetime import datetime, timedelta
from typing import Dict, Any

class ETAPredictor:
    """
    Data-driven ETA prediction engine accounting for speed, road topology,
    traffic congestion factors, and driver mandatory rest stops.
    """
    def predict_eta(
        self,
        current_time: datetime,
        remaining_distance_km: float,
        traffic_condition: str = "Moderate",
        weather_condition: str = "Clear",
        current_delay_min: int = 0
    ) -> Dict[str, Any]:
        
        # Base speed 70 km/h on highway corridors
        base_speed_kmh = 70.0
        
        # Traffic speed modifiers
        traffic_speed_factors = {
            "Light": 1.1,
            "Moderate": 0.95,
            "Heavy": 0.70,
            "Severe Congestion": 0.45
        }
        
        weather_speed_factors = {
            "Clear": 1.0,
            "Rain": 0.90,
            "Fog": 0.85,
            "Snow": 0.70,
            "Storm": 0.55
        }
        
        speed_factor = (
            traffic_speed_factors.get(traffic_condition, 0.95) * 
            weather_speed_factors.get(weather_condition, 1.0)
        )
        
        effective_speed = max(20.0, base_speed_kmh * speed_factor)
        driving_hours = remaining_distance_km / effective_speed
        driving_minutes = int(driving_hours * 60)
        
        # Mandatory rest stops (30 min every 4.5 hours of driving)
        rest_stop_minutes = int((driving_hours // 4.5) * 30)
        
        total_duration_minutes = driving_minutes + rest_stop_minutes + current_delay_min
        
        calculated_eta = current_time + timedelta(minutes=total_duration_minutes)
        
        return {
            "effective_speed_kmh": round(effective_speed, 1),
            "driving_minutes": driving_minutes,
            "rest_stop_minutes": rest_stop_minutes,
            "delay_minutes": current_delay_min,
            "total_duration_minutes": total_duration_minutes,
            "predicted_eta": calculated_eta.isoformat(),
            "formatted_eta": calculated_eta.strftime("%Y-%m-%d %H:%M UTC")
        }

eta_predictor = ETAPredictor()
