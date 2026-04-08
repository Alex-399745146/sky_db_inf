# src/geocoder.py
"""
Класс NominatimGeocoder по одному названию страны читает из API данные.
Так он остаётся автономным.
"""


from abc import ABC, abstractmethod
from configparser import ConfigParser
import requests


# Абстрактный класс
class BaseGeocoder(ABC):
    """
    Абстрактный класс для получения координат страны из внешнего API.
    Определяет интерфейс: get_country_bounds(country_name: str) -> dict.
    """

    @abstractmethod
    def get_country_bounds(self, country_name: str) -> dict:
        """
        Для заданной страны возвращает границы (bounding box)
        в виде dict с ключами: min_lat, max_lat, min_lon, max_lon.

        Args:
            country_name (str): название страны.

        Returns:
            dict: словарь с координатами границ.
        """
        raise NotImplementedError


# Дочерний класс
class NominatimGeocoder(BaseGeocoder):
    """
    Реализация геокодера через Nominatim (nominatim.openstreetmap.org).
    Читает список стран из config.ini, но метод get_country_bounds
    работает автономно (принимает строку с названием страны).
    """

    def __init__(self, config_path: str = "config/config.ini"):
        """
        Args:
            config_path (str): путь к INI‑файлу.
        """
        self.config_path = config_path
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "KURSOVAYA_3/1.0"})

    def get_country_bounds(self, country_name: str) -> dict:
        """
        Запрашивает у Nominatim границы страны и возвращает как dict.

        Example:
            {
                "min_lat": 41.19,
                "max_lat": 81.86,
                "min_lon": 19.61,
                "max_lon": -169.01
            }

        Args:
            country_name (str): название страны.

        Returns:
            dict: координаты geo_box (min_lat, max_lat, min_lon, max_lon).
        """
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            "country": country_name,
            "format": "json",
            "polygon_geojson": 0,  # не нужен geojson
        }

        response = self.session.get(url, params=params)
        result_data = response.json()

        # Берем первый результат (основная страна)
        if not result_data:
            raise ValueError(f"Country '{country_name}' not found in Nominatim.")

        # Geo box(точки координат): [min_lat, max_lat, min_lon, max_lon]
        geo_box = result_data[0]["boundingbox"]
        return {
            "min_lat": float(geo_box[0]),
            "max_lat": float(geo_box[1]),
            "min_lon": float(geo_box[2]),
            "max_lon": float(geo_box[3]),
        }


if __name__ == "__main__":
    import os

    # Путь к проекту: sky_db_inf.
    main_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # Путь к конфигам ини проекта.
    config_path = os.path.join(main_root, "config", "config.ini")
    print("\nПуть к конфигурациям -", config_path)

    # Читаем конфиги.
    config = ConfigParser()
    config.read(config_path)

    # Проверка, что секция app и countries существуют в конфигах ини.
    countries_str = config.get("app", "countries")
    countries = [c.strip() for c in countries_str.split(",") if c.strip()]

    print("\nСтраны для проверки в конфигах:", type(countries), countries)

    # Проверка API и геокодера.
    geocoder = NominatimGeocoder(config_path)

    for country in countries:
        bounds = geocoder.get_country_bounds(country)
        print(f"\n{country} координаты границы боксов:")
        print(f"  min_lat: {bounds['min_lat']:.4f} - max_lat: {bounds['max_lat']:.4f}")
        print(f"  min_lon: {bounds['min_lon']:.4f} - max_lon: {bounds['max_lon']:.4f}")
