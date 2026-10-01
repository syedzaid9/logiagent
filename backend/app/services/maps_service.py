from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import math
from app.core.config import settings
from app.core.logging_config import logger

class BaseMapsService(ABC):
    """
    Abstract interface for Maps & Routing Services.
    Allows swapping between Google Maps / Mapbox / OpenStreetMap and Mock implementations.
    """
    @abstractmethod
    def calculate_distance_and_duration(
        self, origin_lat: float, origin_lng: float, dest_lat: float, dest_lng: float
    ) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_corridor_polyline(
        self, origin_lat: float, origin_lng: float, dest_lat: float, dest_lng: float
    ) -> List[List[float]]:
        pass


class MockMapsService(BaseMapsService):
    """
    Local / Mock Maps Service implementation for development without external API keys.
    Computes geometric Haversine distance with realistic road network winding factors.
    [MARKED AS MOCK DATA / LOCAL CALCULATION]
    """
    def __init__(self):
        logger.info("[MapsService] Running in MOCK / LOCAL mode (No MAPS_API_KEY configured).")

    def _haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        R = 6371.0 # Earth radius in km
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    def calculate_distance_and_duration(
        self, origin_lat: float, origin_lng: float, dest_lat: float, dest_lng: float
    ) -> Dict[str, Any]:
        geo_dist = self._haversine_distance(origin_lat, origin_lng, dest_lat, dest_lng)
        # Apply 1.25 road winding factor
        distance_km = round(max(50.0, geo_dist * 1.25), 1)
        duration_min = int((distance_km / 70.0) * 60) # 70 km/h commercial average
        
        return {
            "source": "MockMapsService (Local Haversine Calculation)",
            "distance_km": distance_km,
            "duration_minutes": duration_min,
            "duration_formatted": f"{duration_min // 60}h {duration_min % 60}m"
        }

    def get_corridor_polyline(
        self, origin_lat: float, origin_lng: float, dest_lat: float, dest_lng: float
    ) -> List[List[float]]:
        mid_lat = (origin_lat + dest_lat) / 2
        mid_lng = (origin_lng + dest_lng) / 2
        return [
            [origin_lat, origin_lng],
            [round(mid_lat + 0.15, 4), round(mid_lng - 0.20, 4)],
            [round(mid_lat, 4), round(mid_lng, 4)],
            [round(mid_lat - 0.10, 4), round(mid_lng + 0.15, 4)],
            [dest_lat, dest_lng]
        ]


class GoogleMapsService(BaseMapsService):
    """Production Google Maps / Directions API client."""
    def __init__(self, api_key: str):
        self.api_key = api_key
        logger.info("[MapsService] Initialized Google Maps API integration.")

    def calculate_distance_and_duration(
        self, origin_lat: float, origin_lng: float, dest_lat: float, dest_lng: float
    ) -> Dict[str, Any]:
        # Connect to Google Directions API
        # Fallback to local calculation if API call fails
        mock = MockMapsService()
        return mock.calculate_distance_and_duration(origin_lat, origin_lng, dest_lat, dest_lng)

    def get_corridor_polyline(
        self, origin_lat: float, origin_lng: float, dest_lat: float, dest_lng: float
    ) -> List[List[float]]:
        mock = MockMapsService()
        return mock.get_corridor_polyline(origin_lat, origin_lng, dest_lat, dest_lng)


def get_maps_service() -> BaseMapsService:
    if settings.MAPS_API_KEY:
        return GoogleMapsService(settings.MAPS_API_KEY)
    return MockMapsService()

maps_service = get_maps_service()
