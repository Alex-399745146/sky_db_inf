# src/geocoder.py
"""
Класс NominatimGeocoder по одному названию страны читает из API данные.
Так он остаётся автономным.
"""

import os

from dotenv import load_dotenv

load_dotenv()

from abc import ABC, abstractmethod
from typing import Any, Dict

import requests


class BaseGeocoder(ABC):
    """
    Абстрактный класс для получения координат страны из внешнего API.
    Определяет интерфейс: get_country_bounds(country_name: str) -> dict.
    """

    @abstractmethod
    def get_country_bounds(self, country_name: str) -> Dict[str, float]:
        """
        Для заданной страны возвращает границы (bounding box)
        в виде dict с ключами: min_lat, max_lat, min_lon, max_lon.
        """
        raise NotImplementedError


class NominatimGeocoder(BaseGeocoder):
    """
    Геокодер Nominatim: получает границы страны по переданному названию.
    Список стран задаётся вне класса, например через APP_COUNTRIES.
    """

    def __init__(self) -> None:
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "KURSOVAYA_3/1.0"})

    def get_country_bounds(self, country_name: str) -> Dict[str, float]:
        """Запрашивает у Nominatim границы страны и возвращает их словарём."""
        url = "https://nominatim.openstreetmap.org/search"
        params: dict[str, Any] = {
            "country": country_name,
            "format": "json",
            "polygon_geojson": 0,
        }

        response = self.session.get(url, params=params, timeout=30)
        response.raise_for_status()
        result_data: Any = response.json()

        if not result_data:
            raise ValueError(f"Страна «{country_name}» не найдена.")

        geo_box = result_data[0].get("boundingbox")
        if not geo_box or len(geo_box) != 4:
            raise ValueError(f"Nominatim не вернул границы для страны «{country_name}».")

        return {
            "min_lat": float(geo_box[0]),
            "max_lat": float(geo_box[1]),
            "min_lon": float(geo_box[2]),
            "max_lon": float(geo_box[3]),
        }


if __name__ == "__main__":
    countries_str = os.getenv("APP_COUNTRIES", "")
    countries = [country.strip() for country in countries_str.split(",") if country.strip()]

    if not countries:
        raise RuntimeError(
            "Переменная APP_COUNTRIES не задана. Проверьте локальный .env."
        )

    print("Страны для проверки:", countries)

    geocoder = NominatimGeocoder()

    for country in countries:
        bounds = geocoder.get_country_bounds(country)
        print(f"\n{country} — границы:")
        print(f"  min_lat: {bounds['min_lat']:.4f} - max_lat: {bounds['max_lat']:.4f}")
        print(f"  min_lon: {bounds['min_lon']:.4f} - max_lon: {bounds['max_lon']:.4f}")
