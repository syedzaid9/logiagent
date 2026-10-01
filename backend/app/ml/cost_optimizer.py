from typing import Dict, Any, List

class CostOptimizer:
    """
    Cost calculation & optimization engine breaking down fuel, labor, toll,
    and maintenance costs with recommendations for load consolidation.
    """
    def calculate_trip_cost(
        self,
        distance_km: float,
        vehicle_type: str = "Semi-Truck (Dry Van)",
        fuel_price_per_liter: float = 1.15,
        driver_hourly_rate: float = 32.0,
        toll_fees: float = 25.0
    ) -> Dict[str, Any]:
        
        # Fuel consumption in Liters per 100km
        consumption_rates = {
            "Semi-Truck (Dry Van)": 32.0,
            "Reefer (Refrigerated)": 38.0, # Higher due to secondary engine
            "Flatbed": 34.0,
            "Box Truck": 22.0,
            "Sprinter Van": 12.5
        }
        
        liters_per_100km = consumption_rates.get(vehicle_type, 30.0)
        total_fuel_liters = (distance_km / 100.0) * liters_per_100km
        fuel_cost = round(total_fuel_liters * fuel_price_per_liter, 2)
        
        # Labor duration estimate (65 km/h avg)
        trip_hours = max(1.0, distance_km / 65.0)
        driver_cost = round(trip_hours * driver_hourly_rate, 2)
        
        # Maintenance depreciation ($0.15 per km)
        maintenance_cost = round(distance_km * 0.15, 2)
        
        total_cost = round(fuel_cost + driver_cost + toll_fees + maintenance_cost, 2)
        cost_per_km = round(total_cost / distance_km, 2) if distance_km > 0 else 0.0
        
        return {
            "distance_km": distance_km,
            "vehicle_type": vehicle_type,
            "fuel_cost": fuel_cost,
            "driver_cost": driver_cost,
            "toll_cost": toll_fees,
            "maintenance_cost": maintenance_cost,
            "total_cost": total_cost,
            "cost_per_km": cost_per_km,
            "currency": "USD"
        }

cost_optimizer = CostOptimizer()
