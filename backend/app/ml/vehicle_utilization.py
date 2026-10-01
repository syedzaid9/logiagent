from typing import List, Dict, Any

class VehicleUtilizationCalculator:
    """
    Computes capacity utilization across individual vehicles and the entire fleet.
    Utilization = used_capacity_kg / total_capacity_kg
    """
    def calculate_utilization(self, vehicles_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not vehicles_data:
            return {
                "total_vehicles": 0,
                "available_vehicles": 0,
                "active_vehicles": 0,
                "average_utilization_pct": 0.0,
                "by_type": []
            }
            
        total_capacity = 0.0
        total_load = 0.0
        available_count = 0
        active_count = 0
        
        type_stats: Dict[str, Dict[str, Any]] = {}
        
        for v in vehicles_data:
            v_type = v.get("type", "Standard")
            cap = float(v.get("max_capacity_kg", 1.0))
            load = float(v.get("current_load_kg", 0.0))
            status = v.get("status", "Available")
            
            total_capacity += cap
            total_load += load
            
            if status == "Available":
                available_count += 1
            else:
                active_count += 1
                
            if v_type not in type_stats:
                type_stats[v_type] = {
                    "total_count": 0,
                    "active_count": 0,
                    "total_cap": 0.0,
                    "total_load": 0.0
                }
                
            type_stats[v_type]["total_count"] += 1
            if status != "Available":
                type_stats[v_type]["active_count"] += 1
            type_stats[v_type]["total_cap"] += cap
            type_stats[v_type]["total_load"] += load
            
        avg_utilization = round((total_load / total_capacity) * 100.0, 1) if total_capacity > 0 else 0.0
        
        by_type_list = []
        for v_type, s in type_stats.items():
            load_pct = round((s["total_load"] / s["total_cap"]) * 100.0, 1) if s["total_cap"] > 0 else 0.0
            by_type_list.append({
                "vehicle_type": v_type,
                "total_count": s["total_count"],
                "active_count": s["active_count"],
                "average_load_pct": load_pct
            })
            
        return {
            "total_vehicles": len(vehicles_data),
            "available_vehicles": available_count,
            "active_vehicles": active_count,
            "average_utilization_pct": avg_utilization,
            "by_type": by_type_list
        }

vehicle_utilization_calculator = VehicleUtilizationCalculator()
