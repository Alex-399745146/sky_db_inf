# main.py
"""Файл основной логики точки входа."""

import os

from dotenv import load_dotenv
from prettytable import PrettyTable

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

from src.db_creat import create_tables_db, get_re_create_db
from src.db_use import DBManager
from src.sky_data_adapter import SkyDataAdapter

FIRST_RUN_FLAG_NAME = ".first_run_done"

def required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Не задана обязательная переменная {name} в .env.")

    if name == "DB_PASSWORD" and value == "replace-with-your-new-password":
        raise RuntimeError("В DB_PASSWORD оставлен плейсхолдер.")

    return value

def load_countries_from_env() -> list[str]:
    countries = [
        country.strip()
        for country in os.getenv("APP_COUNTRIES", "").split(",")
        if country.strip()
    ]
    if not countries:
        raise RuntimeError("Задайте APP_COUNTRIES в локальном .env.")

    return countries

def load_db_from_env() -> dict:
    return {
        "dbname": required_env("DB_NAME"),
        "user": required_env("DB_USER"),
        "password": required_env("DB_PASSWORD"),
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", "5432")),
    }

def ask_country(default_countries: list[str]) -> list[str]:
    prompt = (
        "Введите страны через запятую "
        f"(Enter — использовать {', '.join(default_countries)}): "
    )
    user_input = input(prompt).strip()

    if not user_input:
        return default_countries

    return [country.strip() for country in user_input.split(",") if country.strip()]

def get_flag_path() -> str:
    return os.path.join(PROJECT_ROOT, "config", FIRST_RUN_FLAG_NAME)

def ask_update_mode() -> str:
    flag_path = get_flag_path()

    if not os.path.exists(flag_path):
        os.makedirs(os.path.dirname(flag_path), exist_ok=True)
        with open(flag_path, "w", encoding="utf-8") as file:
            file.write("ok\n")
        print("Первый запуск программы: выбран режим update.")
        return "update"

    while True:
        answer = input(
            "Обновить данные БД (удалить и пересоздать всю базу)? y/n: "
        ).strip().lower()

        if answer == "y":
            return "update"
        if answer == "n":
            return "append"

        print("Некорректный ввод. Введите 'y' или 'n'.")



# 4.1
def print_countries_and_planes(db: DBManager) -> None:
    """Получает список всех стран и количество самолётов в каждой стране."""
    data = db.get_info_countries_and_planes()
    table = PrettyTable(["Страна", "Кол-во самолётов"])
    for row in data:
        table.add_row([row["country_name"], row["plane_count"]])
    print("\nСтраны и количество самолётов:")
    print(table)


# 4.2
def print_all_planes(db: DBManager) -> None:
    """
    Получает список всех самолётов с указанием страны регистрации,
    номера самолёта, скорость полёта и высота полёта.
    """
    data = db.get_all_planes()
    table = PrettyTable(["icao24", "Страна рег.", "Скорость", "Высота"])
    for row in data:
        table.add_row([row["icao24"], row["country_code"], row["velocity"], row["altitude"]])
    print("\nВсе самолёты:")
    print(table)


# 4.3
def print_avg_height(db: DBManager) -> None:
    """Получает среднюю высоту полёта всех самолётов."""
    avg = db.get_avg_height()
    print(f"\nСредняя высота полёта всех самолётов: {avg:.2f}")


# 4.4
def print_max_height_planes(db: DBManager) -> None:
    """Список всех самолётов, у которых высота полёта выше средней."""
    data = db.get_max_height()
    table = PrettyTable(["icao24", "country_id", "Скорость", "Высота"])
    for row in data:
        table.add_row([row["icao24"], row["country_id"], row["velocity"], row["altitude"]])
    print("\nСамолёты выше средней высоты:")
    print(table)


# 4.5
def print_planes_by_countries(db: DBManager, countries: list) -> None:
    """Список всех самолётов, зарегистрированных в странах названии которых взяты в работу."""
    data = db.get_planes_by_countries(countries)
    table = PrettyTable(["icao24", "Страна рег.", "Скорость", "Высота"])
    for row in data:
        table.add_row([row["icao24"], row["country_code"], row["velocity"], row["altitude"]])
    print("Самолёты с домашней регистрацией:")
    print(table)


def main() -> None:
    """Основной алгоритм запуска программы."""
    default_countries = load_countries_from_env()
    countries = ask_country(default_countries)
    db_cfg = load_db_from_env()
    mode = ask_update_mode()

    if mode == "update":
        print("Пересоздаём БД и таблицы...")
        get_re_create_db(
            db_name=db_cfg["dbname"],
            user=db_cfg["user"],
            password=db_cfg["password"],
            host=db_cfg["host"],
            port=db_cfg["port"],
        )
    else:
        print("Дополняем существующие данные...")

    create_tables_db(
        db_name=db_cfg["dbname"],
        user=db_cfg["user"],
        password=db_cfg["password"],
        host=db_cfg["host"],
        port=db_cfg["port"],
    )

    db = DBManager(
        dbname=db_cfg["dbname"],
        user=db_cfg["user"],
        password=db_cfg["password"],
        host=db_cfg["host"],
        port=db_cfg["port"],
    )

    adapter = SkyDataAdapter()

    try:
        for country in countries:
            print(f"\nПолучаем самолёты для страны: {country}")
            adapter.get_aeroplanes(country)

            if adapter.aeroplanes is None:
                print("  → Данные не получены из API.")
                continue

            country_id = db.ensure_country(country)

            for aircraft in adapter.aeroplanes:
                aircraft_id = db.ensure_aircraft(aircraft)
                db.insert_observation(
                    aircraft_id,
                    country_id,
                    aircraft["position_time"],
                )

        print_countries_and_planes(db)
        print_all_planes(db)
        print_avg_height(db)
        print_max_height_planes(db)
        print_planes_by_countries(db, countries)
    finally:
        db.close()

if __name__ == "__main__":
    main()
