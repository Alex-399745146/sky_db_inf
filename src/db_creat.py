# src/db_creat.py
"""Создание БД, только создание/пересоздание
таблиц нет смысла делать на основе классов ООП
сделано на чистых функциях так проще и понятнее.
"""


import psycopg2



def get_re_create_db(
    db_name: str,
    user: str,
    password: str,
    host: str = "localhost",
    port: int = 5432,
):
    """
    Создаёт/пересоздаёт БД PostgreSQL (удаляет старую, создаёт новую).
    """
    # Подключаемся к серверу без выбора БД
    conn = psycopg2.connect(
        user=user,
        password=password,
        host=host,
        port=port,
    )
    conn.autocommit = True  # включаем autocommit
    cur = conn.cursor()

    cur.execute(f"DROP DATABASE IF EXISTS {db_name};")
    cur.execute(f"CREATE DATABASE {db_name};")

    print(f"База данных - '{db_name}' пересоздана.")

    cur.close()
    conn.close()


def create_tables_db(
    db_name: str,
    user: str,
    password: str,
    host: str = "localhost",
    port: int = 5432,
):
    """
    Создаёт таблицы в БД db_sky по (3NF).
    """
    conn = psycopg2.connect(
        dbname=db_name,
        user=user,
        password=password,
        host=host,
        port=port,
    )
    conn.autocommit = True  # Авто сохранение.
    cur = conn.cursor()

    # Создание таблицы стран.
    cur.execute("""
        CREATE TABLE IF NOT EXISTS countries (
            country_id SERIAL PRIMARY KEY,
            country_name VARCHAR(100) NOT NULL UNIQUE
        );
    """)

    # Создание таблицы страны в которых зарегистрированные самолёты.
    cur.execute("""
        CREATE TABLE IF NOT EXISTS aircraft_countries (
            country_id SERIAL PRIMARY KEY,
            country_code VARCHAR(10) NOT NULL UNIQUE
        );
    """)

    # Создание таблицы данных по самолётам.
    cur.execute("""
        CREATE TABLE IF NOT EXISTS aircraft (
            aircraft_id SERIAL PRIMARY KEY,
            fly_code VARCHAR(6) NOT NULL UNIQUE,
            callsign VARCHAR(16),
            latitude REAL,
            longitude REAL,
            altitude REAL,
            velocity REAL,
            on_ground BOOLEAN,
            country_id INTEGER REFERENCES aircraft_countries(country_id)
        );
    """)

    # Связующая таблица существующих отношений.
    cur.execute("""
        CREATE TABLE IF NOT EXISTS flight_observations (
            observation_id SERIAL PRIMARY KEY,
            aircraft_id INTEGER REFERENCES aircraft(aircraft_id),
            country_id INTEGER REFERENCES countries(country_id),
            observed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    print("Таблицы, созданны в третьей нормальной форме.")

    cur.close()
    conn.close()


if __name__ == "__main__":
    db_name, user, password = "db_sky", "postgres", "399745146"

    get_re_create_db(db_name, user, password)
    create_tables_db(db_name, user, password)
