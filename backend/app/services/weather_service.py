from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from app.core.config import settings
from app.core.logging_config import logger

class BaseWeatherService(ABC):
    @abstractmethod
    def get_weather_forecast(self, latitude: float, longitude: float) -> Dict[str, Any]:
        pass

class MockWeatherService(BaseWeatherService):
    """
    Mock Weather Service for development without WEATHER_API_KEY.
    [MARKED AS MOCK DATA / LOCAL CALCULATION]
    """
    def __init__(self):
        logger.info("[WeatherService] Running in MOCK mode (No WEATHER_API_KEY configured).")

    def get_weather_forecast(self, latitude: float, longitude: float) -> Dict[str, Any]:
        return {
            "source": "MockWeatherService (Local Clear Weather Default)",
            "condition": "Clear",
            "temperature_celsius": 21.5,
            "precipitation_probability": 10,
            "visibility_km": 10.0,
            "adverse_delay_factor": 1.0
        }

class OpenWeatherService(BaseWeatherService):
    def __init__(self, api_key: str):
        self.api_key = api_key
        logger.info("[WeatherService] Initialized OpenWeather API client.")

    def get_weather_forecast(self, latitude: float, longitude: float) -> Dict[str, Any]:
        return MockWeatherService().get_weather_forecast(latitude, longitude)

def get_weather_service() -> BaseWeatherService:
    if settings.WEATHER_API_KEY:
        return OpenWeatherService(settings.WEATHER_API_KEY)
    return MockWeatherService()

weather_service = get_weather_service()
