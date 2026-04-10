# src/db_use.py
"""Управление и работа с уже созданной БД"""


import configparser
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


class DatabaseManager:
    """
    Класс для управления БД PostgreSQL:
    - проверка существования БД,
    - удаление старой версии,
    - создание новой БД,
    - создание таблиц в 3NF.
    """

    def __init__(self, config_path: str = "config/config.ini"):
        """
        Args:
            config_path (str): путь к INI‑файлу с настройками БД.
        """
        self.config_path = config_path
        self._config = self._read_config()
        self._conn_params = {
            "user": self._config["db"]["user"],
            "password": self._config["db"]["password"],
            "host": self._config["db"]["host"],
            "port": self._config["db"]["port"],
        }

    def _read_config(self) -> configparser.ConfigParser:
        """Читает конфиг‑файл и возвращает ConfigParser."""
        config = configparser.ConfigParser()
        config.read(self.config_path)
        return config

    def _connect_to_postgres(self):
        """
        Подключается к экземпляру PostgreSQL (без выбора БД).
        """
        return psycopg2.connect(**self._conn_params)

    def drop_and_create_db(self):
        """
        Проверяет существование БД db_sky_list,
        при наличии удаляет её и создаёт заново.
        """
        conn = self._connect_to_postgres()
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()

        dbname = self._config["db"]["dbname"]

        # Удаляем БД, если существует
        cur.execute(f"DROP DATABASE IF EXISTS {dbname};")

        # Создаём БД
        cur.execute(f"CREATE DATABASE {dbname};")
        print(f"Database {dbname} created.")

        cur.close()
        conn.close()

    def create_tables(self):
        """
        Создаёт таблицы в БД db_sky_list:
        - countries (страны),
        - aircraft (самолёты),
        - aircraft_countries (страна регистрации самолёта).

        Структура приведена до 3NF.
        """
        conn = psycopg2.connect(
            dbname=self._config["db"]["dbname"],
            **self._conn_params
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()

        # Таблица стран
        cur.execute("""
            CREATE TABLE IF NOT EXISTS countries (
                country_id SERIAL PRIMARY KEY,
                country_name VARCHAR(100) NOT NULL UNIQUE
            );
        """)

        # Таблица стран регистрации самолётов
        cur.execute("""
            CREATE TABLE IF NOT EXISTS aircraft_countries (
                country_id SERIAL PRIMARY KEY,
                country_code VARCHAR(10) NOT NULL UNIQUE
            );
        """)

        # Таблица самолётов
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
                country_id INTEGER REFERENCES aircraft_countries(country_id),
                observed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # Связь самолёта с страной исследования (по координатам)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS flight_observations (
                observation_id SERIAL PRIMARY KEY,
                aircraft_id INTEGER REFERENCES aircraft(aircraft_id),
                country_id INTEGER REFERENCES countries(country_id),
                observed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        print("Tables created in 3NF.")

        cur.close()
        conn.close()