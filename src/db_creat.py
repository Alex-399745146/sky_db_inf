# src/db_creat.py
"""Создание и пересоздание базы данных и таблиц."""

import os

import psycopg2
from dotenv import load_dotenv
from psycopg2 import sql

# Локально загружает .env, если файл существует.
# В Compose настройки может передать само окружение контейнера.
load_dotenv()

def get_re_create_db(
    db_name: str,
    user: str,
    password: str,
    host: str = "localhost",
    port: int = 5432,
) -> None:
    """Удаляет существующую БД и создаёт её заново."""
    conn = psycopg2.connect(
        dbname="postgres",
        user=user,
        password=password,
        host=host,
        port=port,
    )
    conn.autocommit = True

    try:
        with conn.cursor() as cur:
            # Имя базы — SQL-идентификатор, поэтому безопасно оформляем его
            # через psycopg2.sql.Identifier, а не подставляем в f-строку.
            cur.execute(
                sql.SQL("DROP DATABASE IF EXISTS {}").format(
                    sql.Identifier(db_name)
                )
            )
            cur.execute(
                sql.SQL("CREATE DATABASE {}").format(
                    sql.Identifier(db_name)
                )
            )

        print(f"База данных '{db_name}' пересоздана.")
    finally:
        conn.close()

def create_tables_db(
    db_name: str,
    user: str,
    password: str,
    host: str = "localhost",
    port: int = 5432,
) -> None:
    """Создаёт таблицы в базе данных."""
    conn = psycopg2.connect(
        dbname=db_name,
        user=user,
        password=password,
        host=host,
        port=port,
    )
    conn.autocommit = True

    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS countries (
                    country_id SERIAL PRIMARY KEY,
                    country_name VARCHAR(100) NOT NULL UNIQUE
                );
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS aircraft_countries (
                    country_id SERIAL PRIMARY KEY,
                    country_code VARCHAR(100) NOT NULL UNIQUE
                );
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS aircraft (
                    aircraft_id SERIAL PRIMARY KEY,
                    icao24 VARCHAR(6) NOT NULL UNIQUE,
                    callsign VARCHAR(16),
                    latitude REAL,
                    longitude REAL,
                    altitude REAL,
                    velocity REAL,
                    on_ground BOOLEAN,
                    country_id INTEGER
                        REFERENCES aircraft_countries(country_id)
                );
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS flight_observations (
                    observation_id SERIAL PRIMARY KEY,
                    aircraft_id INTEGER
                        REFERENCES aircraft(aircraft_id),
                    country_id INTEGER
                        REFERENCES countries(country_id),
                    observed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    position_time BIGINT
                );
            """)

            cur.execute("""
                ALTER TABLE flight_observations
                ADD COLUMN IF NOT EXISTS position_time BIGINT;
            """)

            cur.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS
                    uq_flight_observations_aircraft_position_time
                ON flight_observations (aircraft_id, position_time);
            """)

        print("Таблицы созданы.")
    finally:
        conn.close()

def _required_env(name: str) -> str:
    """Возвращает обязательную переменную окружения."""
    value = os.getenv(name)

    if not value:
        raise RuntimeError(
            f"Не задана переменная окружения {name}. "
            "Проверьте локальный .env."
        )

    if name == "DB_PASSWORD" and value == "replace-with-your-new-password":
        raise RuntimeError(
            "В DB_PASSWORD оставлен плейсхолдер. "
            "Укажите настоящий пароль в локальном .env."
        )

    return value

if __name__ == "__main__":
    db_name = _required_env("DB_NAME")
    user = _required_env("DB_USER")
    password = _required_env("DB_PASSWORD")
    host = os.getenv("DB_HOST", "localhost")
    port = int(os.getenv("DB_PORT", "5432"))

    get_re_create_db(db_name, user, password, host, port)
    create_tables_db(db_name, user, password, host, port)
