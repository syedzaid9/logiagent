from datetime import datetime, timedelta
from typing import List, Dict, Any

class DemandForecaster:
    """
    Time-series demand forecasting module predicting daily logistics shipment load
    across regional distribution centers over a 7-day forward horizon.
    """
    def forecast_demand(self, base_volume: int = 42, days_ahead: int = 7) -> List[Dict[str, Any]]:
        forecasts = []
        now = datetime.utcnow()
        
        # Day of week seasonality factors (Mon: 1.15, Tue: 1.10, Wed: 1.05, Thu: 1.12, Fri: 1.25, Sat: 0.70, Sun: 0.40)
        dow_multipliers = [1.15, 1.10, 1.05, 1.12, 1.25, 0.70, 0.40]
        
        for i in range(1, days_ahead + 1):
            target_date = now + timedelta(days=i)
            dow = target_date.weekday()
            multiplier = dow_multipliers[dow]
            
            # Subtle growth trend + seasonality
            predicted = int(base_volume * multiplier * (1.0 + (i * 0.01)))
            margin = int(predicted * 0.12)
            
            forecasts.append({
                "date": target_date.strftime("%Y-%m-%d"),
                "day_name": target_date.strftime("%a"),
                "predicted_shipments": predicted,
                "lower_bound": max(5, predicted - margin),
                "upper_bound": predicted + margin,
                "expected_fleet_required": int(predicted * 0.75)
            })
            
        return forecasts

demand_forecaster = DemandForecaster()
