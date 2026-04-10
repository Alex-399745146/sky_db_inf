# src/sky_api.py
"""
Клиент API самолётов из OpenSky
"""

from abc import ABC, abstractmethod
from configparser import ConfigParser
from typing import Dict, List

import requests


class BaseAircraftClient(ABC):
    """
    Абстрактный клиент для получения данных о самолётах в заданной области.
    Определяет интерфейс: get_aircraft_in_area(bounds: dict) -> List[Dict].
    """

    @abstractmethod
    def get_aircraft_in_area(self, bounds: dict) -> List[Dict]:
        """
        Возвращает список самолётов в прямоугольной области (bounding box).

        Args:
            bounds (dict): границы области (min_lat, max_lat, min_lon, max_lon).

        Returns:
            List[Dict]: список словарей с данными о самолётах.
        """
        raise NotImplementedError


class OpenSkyAircraftClient(BaseAircraftClient):
    """
    Клиент для OpenSky Network API (https://opensky-network.org).
    Работает по координатам области (geo_box) и возвращает состояние самолётов.
    """

    def __init__(self, username: str, password: str):
        """
        Args:
            username (str): учётная запись OpenSky.
            password (str): пароль.
        """
        self.base_url = "https://opensky-network.org/api/states/all"
        self.auth = (username, password)

    def get_aircraft_in_area(self, bounds: dict) -> List[Dict]:
        """
        Запрашивает самолёты в прямоугольной области.

        Args:
            bounds (dict): словарь с ключами:
                           min_lat, max_lat, min_lon, max_lon.

        Returns:
            List[Dict]: список самолётов (каждый самолёт — dict).
        """
        params = {
            "lamin": bounds["min_lat"],
            "lamax": bounds["max_lat"],
            "lomin": bounds["min_lon"],
            "lomax": bounds["max_lon"],
        }

        response = requests.get(self.base_url, auth=self.auth, params=params)
        result_data = response.json()

        # Проверяем поле "states" JSON ответа, если None то ответ пуст возвращаем [].
        if not result_data.get("states"):
            return []

        # Сырой формат от OpenSky форматирует в удобный для дальнейшей работы вид.
        aircraft_list = []
        for state in result_data["states"]:
            if state is None:
                continue
            aircraft_list.append(
                {
                    "icao24": state[0],
                    "callsign": state[1].strip() if state[1] else None,
                    "country": state[2].strip() if state[2] else None,
                    "latitude": state[6],
                    "longitude": state[5],
                    "altitude": state[13],
                    "velocity": state[9],
                    "on_ground": state[8],
                }
            )

        return aircraft_list


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

    # Учётные данные OpenSky (временно прописываем; можно потом вынести в config.ini).
    opensky_user = "User-Agent"
    opensky_pass = "test-app/1.0"

    # Пример geo_box (Россия или какая‑то область).
    test_bounds = {
        "min_lat": 41.18,
        "max_lat": 82.05,
        "min_lon": -180.0,
        "max_lon": 180.0,
    }

    # Проверка клиента OpenSky.
    client = OpenSkyAircraftClient(username=opensky_user, password=opensky_pass)
    print("Запрашиваю воздушное судно в этом районе:", test_bounds)

    # Выводим кол-во обнаруженных самолётов в указанном geo_box.
    aircraft_list = client.get_aircraft_in_area(test_bounds)
    print(f"Нашел {len(aircraft_list)} воздушное судно.")

    # Выведем первые 3 самолёта для проверки структуры.
    for i, ac in enumerate(aircraft_list[:3]):
        print(f"\nСамолёт {i + 1}:")
        print(f"  icao24:      {ac['icao24']}")
        print(f"  callsign:    {ac['callsign']}")
        print(f"  country:     {ac['country']}")
        print(f"  latitude:    {ac['latitude']}")
        print(f"  longitude:   {ac['longitude']}")
        print(f"  altitude:    {ac['altitude']}")
        print(f"  velocity:    {ac['velocity']}")
        print(f"  on_ground:   {ac['on_ground']}")
