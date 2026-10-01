from typing import Dict, Any

class RouteEfficiencyAnalyzer:
    """
    Analyzes route variance comparing planned vs actual mileage and duration.
    Detects unauthorized detours, traffic bottlenecks, and computes fuel efficiency scores.
    """
    def analyze_route(
        self,
        planned_distance_km: float,
        actual_distance_km: float,
        planned_duration_min: int,
        actual_duration_min: int
    ) -> Dict[str, Any]:
        
        distance_variance_km = actual_distance_km - planned_distance_km
        distance_variance_pct = (distance_variance_km / planned_distance_km) * 100 if planned_distance_km > 0 else 0
        
        duration_variance_min = actual_duration_min - planned_duration_min
        duration_variance_pct = (duration_variance_min / planned_duration_min) * 100 if planned_duration_min > 0 else 0
        
        # Efficiency score 100 minus penalties for distance and duration excess
        score = 100.0 - max(0.0, distance_variance_pct * 1.5) - max(0.0, duration_variance_pct * 0.8)
        efficiency_score = round(max(10.0, min(100.0, score)), 1)
        
        detour_detected = distance_variance_pct > 8.0
        
        return {
            "planned_distance_km": planned_distance_km,
            "actual_distance_km": actual_distance_km,
            "distance_variance_km": round(distance_variance_km, 1),
            "distance_variance_pct": round(distance_variance_pct, 1),
            "planned_duration_min": planned_duration_min,
            "actual_duration_min": actual_duration_min,
            "duration_variance_min": duration_variance_min,
            "efficiency_score": efficiency_score,
            "detour_detected": detour_detected,
            "assessment": (
                "Highly optimal route execution." if efficiency_score >= 90
                else "Acceptable operational variance." if efficiency_score >= 75
                else "Suboptimal route with significant detour or congestion delays."
            )
        }

route_efficiency_analyzer = RouteEfficiencyAnalyzer()
