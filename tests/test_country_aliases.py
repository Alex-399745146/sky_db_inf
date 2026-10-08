import pytest

from src.db_use import DBManager

class FakeCursor:
    def __init__(self):
        self.query = None
        self.params = None

    def execute(self, query, params):
        self.query = query
        self.params = params

    def fetchall(self):
        return [("151d55", "Russian Federation", 268.53, None)]

    def close(self):
        pass

class FakeConnection:
    def __init__(self):
        self.fake_cursor = FakeCursor()

    def cursor(self):
        return self.fake_cursor

@pytest.mark.parametrize("country", ["Russia", "Russian Federation"])
def test_country_aliases_find_russian_federation(country):
    db = DBManager.__new__(DBManager)
    db.conn = FakeConnection()

    result = db.get_planes_by_countries([country])

    assert db.conn.fake_cursor.params == ("russia", "russian federation")
    assert result == [
        {
            "icao24": "151d55",
            "country_code": "Russian Federation",
            "velocity": 268.53,
            "altitude": None,
        }
    ]
