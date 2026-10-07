# src/sky_api.py
"""Клиент OpenSky Network API."""

import os
import time
from typing import Dict, List, Optional

import requests
from dotenv import load_dotenv

load_dotenv()

TOKEN_URL = (
    "https://auth.opensky-network.org/auth/realms/opensky-network/"
    "protocol/openid-connect/token"
)

class OpenSkyAircraftClient:
    """Получает данные о самолётах из OpenSky."""

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
    ) -> None:
        self.base_url = "https://opensky-network.org/api/states/all"

        self.client_id = client_id or os.getenv("OPENSKY_CLIENT_ID") or None
        self.client_secret = (
            client_secret or os.getenv("OPENSKY_CLIENT_SECRET") or None
        )

        if bool(self.client_id) != bool(self.client_secret):
            raise ValueError(
                "Для OpenSky нужно задать обе переменные: "
                "OPENSKY_CLIENT_ID и OPENSKY_CLIENT_SECRET."
            )

        self.session = requests.Session()
        self._access_token: Optional[str] = None
        self._token_expires_at = 0.0

    def _get_access_token(self) -> Optional[str]:
        """Возвращает действующий OAuth2-токен или None для анонимного запроса."""
        if not self.client_id or not self.client_secret:
            return None

        if (
            self._access_token
            and time.monotonic() < self._token_expires_at
        ):
            return self._access_token

        response = self.session.post(
            TOKEN_URL,
            data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=30,
        )
        response.raise_for_status()

        token_data = response.json()
        self._access_token = token_data["access_token"]
        expires_in = int(token_data.get("expires_in", 1800))
        self._token_expires_at = time.monotonic() + max(expires_in - 30, 0)

        return self._access_token

    def get_aircraft_in_area(self, bounds: dict) -> List[Dict]:
        """Возвращает самолёты в заданной области."""
        params = {
            "lamin": bounds["min_lat"],
            "lamax": bounds["max_lat"],
            "lomin": bounds["min_lon"],
            "lomax": bounds["max_lon"],
        }

        headers = {}
        token = self._get_access_token()
        if token:
            headers["Authorization"] = f"Bearer {token}"

        response = self.session.get(
            self.base_url,
            params=params,
            headers=headers,
            timeout=30,
        )
        response.raise_for_status()
        result_data = response.json()

        if not result_data or not result_data.get("states"):
            return []

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
