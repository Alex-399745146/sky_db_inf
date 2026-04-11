# src/db_use.py

from typing import Any, Dict, List, Optional

import psycopg2


class DBManager:
    def __init__(self, dbname: str, user: str, password: str, host: str = "localhost", port: int = 5432):
        self.conn = psycopg2.connect(
            dbname=dbname,
            user=user,
            password=password,
            host=host,
            port=port,
        )
        self.conn.autocommit = True

    # ---------- МЕТОДЫ ВСТАВКИ ДАННЫХ ----------

    def clear_all(self) -> None:
        cur = self.conn.cursor()
        cur.execute("TRUNCATE flight_observations RESTART IDENTITY CASCADE;")
        cur.execute("TRUNCATE aircraft RESTART IDENTITY CASCADE;")
        cur.execute("TRUNCATE aircraft_countries RESTART IDENTITY CASCADE;")
        cur.execute("TRUNCATE countries RESTART IDENTITY CASCADE;")
        cur.close()

    def ensure_country(self, country_name: str) -> int:
        cur = self.conn.cursor()
        cur.execute("SELECT country_id FROM countries WHERE country_name = %s;", (country_name,))
        row = cur.fetchone()
        if row is not None:
            country_id: int = int(row[0])
            cur.close()
            return country_id
        cur.execute(
            "INSERT INTO countries (country_name) VALUES (%s) RETURNING country_id;",
            (country_name,),
        )
        new_row = cur.fetchone()
        assert new_row is not None
        new_id: int = int(new_row[0])
        cur.close()
        return new_id

    def ensure_aircraft_country(self, country_code: Optional[str]) -> Optional[int]:
        if country_code is None:
            return None
        cur = self.conn.cursor()
        cur.execute("SELECT country_id FROM aircraft_countries WHERE country_code = %s;", (country_code,))
        row = cur.fetchone()
        if row is not None:
            country_id: int = int(row[0])
            cur.close()
            return country_id
        cur.execute(
            "INSERT INTO aircraft_countries (country_code) VALUES (%s) RETURNING country_id;",
            (country_code,),
        )
        new_row = cur.fetchone()
        assert new_row is not None
        new_id: int = int(new_row[0])
        cur.close()
        return new_id

    def ensure_aircraft(self, ac: Dict[str, Any]) -> int:
        """
        Приходит в конструкции с такими ключами: dict из OpenSkyAircraftClient:
        {
            "icao24": ...,
            "callsign": ...,
            "country": ...,
            "latitude": ...,
            "longitude": ...,
            "altitude": ...,
            "velocity": ...,
            "on_ground": ...
        }
        """
        cur = self.conn.cursor()
        cur.execute("SELECT aircraft_id FROM aircraft WHERE icao24 = %s;", (ac["icao24"],))
        row = cur.fetchone()
        if row is not None:
            aircraft_id: int = int(row[0])
            cur.execute(
                """
                UPDATE aircraft
                SET callsign = %s,
                    latitude = %s,
                    longitude = %s,
                    altitude = %s,
                    velocity = %s,
                    on_ground = %s
                WHERE aircraft_id = %s;
                """,
                (
                    ac["callsign"],
                    ac["latitude"],
                    ac["longitude"],
                    ac["altitude"],
                    ac["velocity"],
                    ac["on_ground"],
                    aircraft_id,
                ),
            )
            cur.close()
            return aircraft_id

        country_id = self.ensure_aircraft_country(ac["country"])
        cur.execute(
            """
            INSERT INTO aircraft (
                icao24, callsign, latitude, longitude,
                altitude, velocity, on_ground, country_id
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            RETURNING aircraft_id;
            """,
            (
                ac["icao24"],
                ac["callsign"],
                ac["latitude"],
                ac["longitude"],
                ac["altitude"],
                ac["velocity"],
                ac["on_ground"],
                country_id,
            ),
        )
        new_row = cur.fetchone()
        assert new_row is not None
        aircraft_id = int(new_row[0])
        cur.close()
        return aircraft_id

    def insert_observation(self, aircraft_id: int, country_id: int) -> None:
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT INTO flight_observations (aircraft_id, country_id)
            VALUES (%s, %s);
            """,
            (aircraft_id, country_id),
        )
        cur.close()

    # ---------- МЕТОДЫ ЗАПРОСОВ К БД ----------

    def get_info_countries_and_planes(self) -> List[Dict[str, Any]]:
        """Получает список всех стран и количество самолётов в каждой стране."""
        query = """
            SELECT
                c.country_name,
                COUNT(fo.aircraft_id) AS plane_count
            FROM countries c
            LEFT JOIN flight_observations fo ON c.country_id = fo.country_id
            GROUP BY c.country_id, c.country_name
            ORDER BY c.country_name;
        """
        cur = self.conn.cursor()
        cur.execute(query)
        rows = cur.fetchall()
        cur.close()
        return [{"country_name": r[0], "plane_count": r[1]} for r in rows]

    def get_all_planes(self) -> List[Dict[str, Any]]:
        """
        Запрос в базу на получение списка всех самолётов с указанием
        страны регистрации,
        номера самолёта,
        скорость полёта и
        высота полёта.
        """
        query = """
            SELECT
                a.icao24,
                ac.country_code,
                a.velocity,
                a.altitude
            FROM aircraft a
            LEFT JOIN aircraft_countries ac ON a.country_id = ac.country_id
            ORDER BY a.icao24;
        """
        cur = self.conn.cursor()
        cur.execute(query)
        rows = cur.fetchall()
        cur.close()
        return [{"icao24": r[0], "country_code": r[1], "velocity": r[2], "altitude": r[3]} for r in rows]

    def get_avg_height(self) -> float:
        """Запрос в базу на получение списка средней высоты полёта всех самолётов."""
        cur = self.conn.cursor()
        cur.execute("SELECT AVG(altitude) FROM aircraft;")
        row = cur.fetchone()
        cur.close()
        avg = row[0] if row is not None else None
        return float(avg) if avg is not None else 0.0

    def get_max_height(self) -> List[Dict[str, Any]]:
        """Запрос в базу на получение список всех самолётов, у которых высота полёта выше средней."""
        avg = self.get_avg_height()
        cur = self.conn.cursor()
        cur.execute(
            "SELECT icao24 , country_id, velocity, altitude FROM aircraft WHERE altitude > %s;",
            (avg,),
        )
        rows = cur.fetchall()
        cur.close()
        return [{"icao24": r[0], "country_id": r[1], "velocity": r[2], "altitude": r[3]} for r in rows]

    def get_planes_by_countries(self, reg_countries: List[str]) -> List[Dict[str, Any]]:
        """
        Запрос в базу на получение списка всех самолётов, зарегистрированных
        в странах названии которых взяты в работу.
        """
        if not reg_countries:
            return []

        placeholders = ",".join(["%s"] * len(reg_countries))
        query = f"""
            SELECT
                a.icao24,
                ac.country_code,
                a.velocity,
                a.altitude
            FROM aircraft a
            JOIN aircraft_countries ac ON a.country_id = ac.country_id
            WHERE ac.country_code IN ({placeholders})
            ORDER BY ac.country_code, a.icao24;
        """
        cur = self.conn.cursor()
        cur.execute(query, tuple(reg_countries))
        rows = cur.fetchall()
        cur.close()
        result = [{"icao24": r[0], "country_code": r[1], "velocity": r[2], "altitude": r[3]} for r in rows]

        return result

    def close(self) -> None:
        if self.conn:
            self.conn.close()
