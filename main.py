# src/main.py
"""Файл основной логики точки входа."""

import os
from configparser import ConfigParser
from typing import Any, Dict

from prettytable import PrettyTable

from src.db_creat import create_tables_db, get_re_create_db
from src.db_use import DBManager
from src.sky_data_adapter import SkyDataAdapter

FIRST_RUN_FLAG_NAME = ".first_run_done"


def get_flag_path(config_path: str) -> str:
    """
    Возвращает путь к флаговому файлу в той же папке, что и config.ini.
    """
    config_dir = os.path.dirname(config_path)
    return os.path.join(config_dir, FIRST_RUN_FLAG_NAME)


# 1.1
def load_countries_from_config(config_path: str) -> list:
    """
    Функция чтения данных из config/config.ini читает
    секцию [app] и возвращает словарь данных со станами.
    """
    config = ConfigParser()  # Пустой объект ConfigParser.
    config.read(config_path)  # Запись данных в объект.
    countries_str = config.get("app", "countries")  # Читает секцию [app].
    result = [c.strip() for c in countries_str.split(",") if c.strip()]  # Разделяем строку для преобразования в лист.

    return result


# 1.2
def ask_country(default_countries: list) -> list:
    """Функция ввода локаций для поиска самолётов в них."""
    user_input = input(
        f"Введите страны через запятую (Enter — ввод стран(ы) из config.ini: {', '.join(default_countries)}): "
    ).strip()
    if not user_input:

        return default_countries
    new_countries: list = [c.strip() for c in user_input.split(",") if c.strip()]  # Преобразуем str -> list.

    return new_countries


# 1.3
def save_countries_to_config(config_path: str, countries: list) -> None:
    """
    Сохраняет список стран в секцию [app] параметр countries в config.ini.
    """
    config = ConfigParser()
    config.read(config_path)
    config.set("app", "countries", ", ".join(countries))

    with open(config_path, "w", encoding="utf-8") as file:
        config.write(file)


# 2.1
def load_db_from_config(config_path: str) -> Dict[str, Any]:
    """
    Функция чтения настроек БД из config.ini читает секцию [db]
    и возвращает словарь параметров для подключения к PostgreSQL.
    """
    config = ConfigParser()  # Пустой объект ConfigParser.
    config.read(config_path)  # Запись данных в объект.
    # Заносим в словарь(input_data_db) данные из секции db.
    input_data_db = {
        "dbname": config.get("db", "dbname"),
        "user": config.get("db", "user"),
        "password": config.get("db", "password"),
        "host": config.get("db", "host"),
        "port": config.getint("db", "port"),
    }

    return input_data_db


# 2.2
def ask_update_mode(config_path: str) -> str:
    """
    При первом запуске всегда возвращает 'update'.
    На последующих запусках функция спрашивает у пользователя режим работы:
    1. update - перезапись,
    2. append - дополнение.
    Возвращает флаги 'update' или 'append'.
    """
    flag_path = get_flag_path(config_path)

    # Если флага нет — первый запуск.
    if not os.path.exists(flag_path):
        os.makedirs(os.path.dirname(flag_path), exist_ok=True)
        with open(flag_path, "w", encoding="utf-8") as f:
            f.write("ok\n")
        print("Первый запуск программы: выполняем полное обновление БД (режим update).")
        return "update"

    while True:
        answer = input("Обновить данные БД (очистить и пересоздать таблицы)? y/n: ").strip().lower()

        if answer == "y":

            return "update"
        if answer == "n":

            return "append"

        print("Некорректный ввод. Пожалуйста, введите 'y' или 'n'.")


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
    print("""\nВНИМАНИЕ результативность зависит от правильности написания страны
Russian Federation-> даст результат, Russia-> покажет 0""")
    print("Самолёты с домашней регистрацией:")
    print(table)


def main() -> None:
    """Основной алгоритм запуска процессов в программе"""
    project_root = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(project_root, "config", "config.ini")

    # 1. Читаем страны по умолчанию(config/config.ini) и предлагаем пользователю ввод своих стран(ы).
    default_countries = load_countries_from_config(config_path)  # 1.1
    user_countries = ask_country(default_countries)  # 1.2

    # Если пользователь ввёл что‑то своё — сохраняем это в config.ini.
    if user_countries != default_countries:
        save_countries_to_config(config_path, user_countries)  # 1.3
        countries = user_countries
    else:
        countries = default_countries

    # 2. Подключаемся к БД и решаем: чистить или дополнять
    db_cfg = load_db_from_config(config_path)  # 2.1

    # mode это результат ввода пользователем y/n.
    mode = ask_update_mode(config_path)  # 2.2

    if mode == "update":
        print("Пересоздаём БД и таблицы...")
        get_re_create_db(db_name=db_cfg["dbname"], user=db_cfg["user"], password=db_cfg["password"])
        create_tables_db(db_name=db_cfg["dbname"], user=db_cfg["user"], password=db_cfg["password"])
    else:
        print("Дополняем существующие данные...")
        # на всякий случай гарантируем, что таблицы есть
        create_tables_db(db_name=db_cfg["dbname"], user=db_cfg["user"], password=db_cfg["password"])

    db = DBManager(
        dbname=db_cfg["dbname"],
        user=db_cfg["user"],
        password=db_cfg["password"],
    )

    # 3. Получаем данные из API и пишем в БД.
    adapter = SkyDataAdapter(config_path)

    for country in countries:
        print(f"\nПолучаем самолёты для страны: {country}")
        adapter.get_aeroplanes(country)

        if adapter.aeroplanes is None:
            print("  → Данные не получены из API.")
            continue

        country_id = db.ensure_country(country)

        for ac in adapter.aeroplanes:
            aircraft_id = db.ensure_aircraft(ac)
            db.insert_observation(aircraft_id, country_id)

    project_root = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(project_root, "config", "config.ini")

    # 4. Вызываем отчёта через PrettyTable.
    print_countries_and_planes(db)  # 4.1
    print_all_planes(db)  # 4.2
    print_avg_height(db)  # 4.3
    print_max_height_planes(db)  # 4.4

    countries_from_config = load_countries_from_config(config_path)
    print_planes_by_countries(db, countries_from_config)  # 4.5

    db.close()


if __name__ == "__main__":
    main()
