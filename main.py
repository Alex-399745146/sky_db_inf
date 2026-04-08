# src/main.py

from configparser import ConfigParser
import os
from src.sky_data_adapter import SkyDataAdapter


def load_countries(config_path: str) -> list:
    """Читает список стран из config.ini."""
    config = ConfigParser()
    config.read(config_path)
    countries_str = config.get("app", "countries")
    return [c.strip() for c in countries_str.split(",") if c.strip()]


def main():
    project_root = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(project_root, "config", "config.ini")

    # print("project_root =", project_root)
    # print("config_path =", config_path)

    # APIAdapter
    adapter = SkyDataAdapter(config_path)

    countries = load_countries(config_path)
    print("Страны для проверки:", countries)

    for country in countries:
        print(f"\nПоиск самолётов в {country}...")
        adapter.get_aeroplanes(country)

        if adapter.aeroplanes is None:
            print("  → Данные не получены.")
            continue

        print(f"  Всего обнаружено {len(adapter.aeroplanes)} самолётов в {country}.")

        # Пример: вывод первых двух самолётов
        for ac in adapter.aeroplanes[:2]:
            print(f"    Номер борта: {ac['id_number']}, "
                  f"Широта: {ac['latitude']}, "
                  f"Долгота: {ac['longitude']}, "
                  f"Высота полёта: {ac['altitude']}, "
                  f"Скорость полёта: {ac['velocity']}")


if __name__ == "__main__":
    main()
