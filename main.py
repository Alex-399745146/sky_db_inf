# src/main.py

import os
from configparser import ConfigParser

from prettytable import PrettyTable

from src.db_creat import create_tables_db
from src.db_use import DBManager
from src.sky_data_adapter import SkyDataAdapter


def load_countries_from_config(config_path: str) -> list:
    config = ConfigParser()
    config.read(config_path)
    countries_str = config.get("app", "countries")
    return [c.strip() for c in countries_str.split(",") if c.strip()]


def ask_country(default_countries: list) -> list:
    user_input = input(
        f"Введите страны через запятую (Enter — взять из config.ini: {', '.join(default_countries)}): "
    ).strip()
    if not user_input:
        return default_countries
    return [c.strip() for c in user_input.split(",") if c.strip()]


def ask_update_mode() -> str:
    """
    Возвращает 'update' или 'append'.
    """
    answer = input("Обновить данные БД (очистить и пересоздать таблицы)? y/n: ").strip().lower()
    if answer == "y":
        return "update"
    return "append"


def print_countries_and_planes(db: DBManager) -> None:
    data = db.get_info_countries_and_planes()
    table = PrettyTable(["Страна", "Кол-во самолётов"])
    for row in data:
        table.add_row([row["country_name"], row["plane_count"]])
    print("\nСтраны и количество самолётов:")
    print(table)


def print_all_planes(db: DBManager) -> None:
    data = db.get_all_planes()
    table = PrettyTable(["icao24", "Страна рег.", "Скорость", "Высота"])
    for row in data:
        table.add_row([row["icao24"], row["country_code"], row["velocity"], row["altitude"]])
    print("\nВсе самолёты:")
    print(table)


def print_avg_height(db: DBManager) -> None:
    avg = db.get_avg_height()
    print(f"\nСредняя высота полёта всех самолётов: {avg:.2f}")


def print_max_height_planes(db: DBManager) -> None:
    data = db.get_max_height()
    table = PrettyTable(["icao24", "country_id", "Скорость", "Высота"])
    for row in data:
        table.add_row([row["icao24"], row["country_id"], row["velocity"], row["altitude"]])
    print("\nСамолёты выше средней высоты:")
    print(table)


def print_planes_by_countries(db: DBManager, countries: list) -> None:
    data = db.get_planes_by_countries(countries)
    table = PrettyTable(["icao24", "Страна рег.", "Скорость", "Высота"])
    for row in data:
        table.add_row([row["icao24"], row["country_code"], row["velocity"], row["altitude"]])
    print(f"\nСамолёты, зарегистрированные в странах {countries}:")
    print(table)


def main() -> None:
    project_root = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(project_root, "config", "config.ini")

    # 1. читаем страны по умолчанию и спрашиваем пользователя
    default_countries = load_countries_from_config(config_path)
    countries = ask_country(default_countries)

    # 2. подключаемся к БД и решаем: чистить или дополнять
    db = DBManager(
        dbname="db_sky",
        user="postgres",
        password="399745146",
    )

    mode = ask_update_mode()
    if mode == "update":
        print("Очищаем таблицы и заполняем заново...")
        create_tables_db(
            db_name="db_sky",
            user="postgres",
            password="399745146",
        )  # на случай, если таблиц нет
        db.clear_all()
    else:
        print("Дополняем существующие данные...")

    # 3. получаем данные из API и пишем в БД
    adapter = SkyDataAdapter(config_path)

    for country in countries:
        print(f"\nПолучаем самолёты для страны: {country}")
        adapter.get_aeroplanes(country)

        if adapter.aeroplanes is None:
            print("  → Данные не получены.")
            continue

        country_id = db.ensure_country(country)

        for ac in adapter.aeroplanes:
            aircraft_id = db.ensure_aircraft(ac)
            db.insert_observation(aircraft_id, country_id)

    project_root = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(project_root, "config", "config.ini")

    # 4. Вызываем все методы DBManager и выводим через PrettyTable
    print_countries_and_planes(db)
    print_all_planes(db)
    print_avg_height(db)
    print_max_height_planes(db)

    countries_from_config = load_countries_from_config(config_path)
    print_planes_by_countries(db, countries_from_config)

    db.close()


if __name__ == "__main__":
    main()
