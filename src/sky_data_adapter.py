# src/sky_data_adapter.py
"""
Адаптер объединяющий работу разных модулей(классов) которые интегрированные с
разными внешними публичными API:
- класс NominatimGeocoder
- класс OpenSkyAircraftClient
"""

from typing import Any, Dict, List, Optional

from src.geocoder import NominatimGeocoder
from src.sky_api import OpenSkyAircraftClient


class SkyDataAdapter:
    """
    Адаптер, объединяющий геокод страны и запрос самолётов по координатам.
    Воспроизводит логику старого APIAdapter, но использует отдельные клиенты.
    """

    def __init__(self, config_path: str = "config/config.ini") -> None:
        """
        Args:
            config_path (str): путь к INI‑конфигу.
        """
        self.geocoder = NominatimGeocoder(config_path)
        self.sky_client = OpenSkyAircraftClient(username="User-Agent", password="test-app/1.0")
        self._aeroplanes: Optional[List[Dict[str, Any]]] = None

    @property
    def aeroplanes(self) -> Optional[List[Dict[str, Any]]]:
        """
        Возвращает последний полученный ответ от OpenSky в формате dict.
        Может быть None, если последний запрос был неудачным.
        """
        return self._aeroplanes

    def get_aeroplanes(self, country: str) -> None:
        """
        Получает самолёты, находящиеся в координатах заданной страны.

        Args:
            country (str): название страны (например, 'Russia').
        """
        bounds = self.geocoder.get_country_bounds(country)
        self._aeroplanes = self.sky_client.get_aircraft_in_area(bounds)
