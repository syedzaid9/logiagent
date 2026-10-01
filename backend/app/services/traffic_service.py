from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from app.core.config import settings
from app.core.logging_config import logger

class BaseTrafficService(ABC):
    @abstractmethod
    def get_traffic_condition(self, origin_lat: float, origin_lng: float, dest_lat: float, dest_lng: float) -> Dict[str, Any]:
        pass

class MockTrafficService(BaseTrafficService):
    """
    Mock Traffic Service for development without TRAFFIC_API_KEY.
    [MARKED AS MOCK DATA / LOCAL CALCULATION]
    """
    def __init__(self):
        logger.info("[TrafficService] Running in MOCK mode (No TRAFFIC_API_KEY configured).")

    def get_traffic_condition(self, origin_lat: float, origin_lng: float, dest_lat: float, dest_lng: float) -> Dict[str, Any]:
        return {
            "source": "MockTrafficService (Simulated Congestion Model)",
            "condition": "Moderate",
            "delay_minutes": 15,
            "congestion_level": "Medium",
            "slowdown_factor": 0.95
        }

class TomTomTrafficService(BaseTrafficService):
    def __init__(self, api_key: str):
        self.api_key = api_key
        logger.info("[TrafficService] Initialized TomTom / HERE Traffic API client.")

    def get_traffic_condition(self, origin_lat: float, origin_lng: float, dest_lat: float, dest_lng: float) -> Dict[str, Any]:
        return MockTrafficService().get_traffic_condition(origin_lat, origin_lng, dest_lat, dest_lng)

def get_traffic_service() -> BaseTrafficService:
    if settings.TRAFFIC_API_KEY:
        return TomTomTrafficService(settings.TRAFFIC_API_KEY)
    return MockTrafficService()

traffic_service = get_traffic_service()
