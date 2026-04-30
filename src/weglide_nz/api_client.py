"""WeGlide API client wrapper."""

import weglide_client
import requests
from weglide_client import Club, User
from weglide_client.models import FlightRankList
from weglide_client.api import club_api, flight_api, user_api, auth_api
from weglide_client.rest import ApiException
from pydantic import ValidationError
from dataclasses import dataclass, field
from datetime import date
from typing import Iterator, Any


DEFAULT_HOST = "https://api.weglide.org"
DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"


class APIError(Exception):
    """API error."""


@dataclass
class APIAirport:
    """Wrapper for airport from API response."""
    id: int
    name: str
    latitude: float = 0.0
    longitude: float = 0.0


@dataclass
class APIFlight:
    """Wrapper for flight from API response."""
    id: int
    user_id: int
    user_name: str = ""
    date: str = ""
    points: float = 0.0
    distance: float = 0.0
    airport: APIAirport | None = None
    club_id: int | None = None


@dataclass
class MockFlight:
    """Mock flight for testing."""
    id: int
    user_id: int
    user: Any = None
    date: str = ""
    points: float = 0.0
    airport: Any = None
    club_id: int | None = None


@dataclass
class WeGlideClient:
    """Wrapper around weglide-client for easier access."""

    host: str = DEFAULT_HOST
    username: str = ""
    password: str = ""
    _client: weglide_client.ApiClient | None = None
    _mock_mode: bool = False
    _mock_data: dict = field(default_factory=dict)
    _token: str | None = None

    def __enter__(self):
        if not self._mock_mode:
            configuration = weglide_client.Configuration(host=self.host)

            if self.username and self.password:
                print(f"Authenticating as {self.username}...")
                self._token = self._authenticate()
                print("Authentication successful")
                configuration.api_key = {"Authorization": self._token}
                configuration.api_key_prefix = {"Authorization": "Bearer"}
            else:
                print("No credentials provided - using public API access")

            self._client = weglide_client.ApiClient(configuration)
            self._client.default_headers["User-Agent"] = DEFAULT_USER_AGENT
        return self

    def _authenticate(self) -> str:
        """Authenticate with username/password and return access token."""
        temp_config = weglide_client.Configuration(host=self.host)
        temp_client = weglide_client.ApiClient(temp_config)
        temp_client.default_headers["User-Agent"] = DEFAULT_USER_AGENT
        auth_api_instance = auth_api.AuthApi(temp_client)
        try:
            result = auth_api_instance.authorize_post_v1_auth_authorize_post(
                username=self.username,
                password=self.password,
                grant_type="password",
            )
            if hasattr(result, "access_token"):
                return result.access_token
            if isinstance(result, dict) and "access_token" in result:
                return result["access_token"]
            raise APIError("Authentication succeeded but no access token found")
        except ApiException as e:
            raise APIError(f"Authentication failed: {e}")

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._client and hasattr(self._client, "close"):
            self._client.close()

    def enable_mock(self, mock_data: dict | None = None):
        """Enable mock mode for testing."""
        self._mock_mode = True
        self._mock_data = mock_data or {}

    def _get_flight_api(self) -> flight_api.FlightApi:
        return flight_api.FlightApi(self._client)

    def _get_user_api(self) -> user_api.UserApi:
        return user_api.UserApi(self._client)

    def _get_club_api(self) -> club_api.ClubApi:
        return club_api.ClubApi(self._client)

    def get_flights(
        self,
        date_from: date | None = None,
        date_to: date | None = None,
        user_id: int | None = None,
        club_id: int | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list:
        """Fetch flights with optional filters."""
        if self._mock_mode:
            flights = self._mock_data.get("flights", [])
            filtered = flights
            if date_from:
                filtered = [f for f in filtered if f.date >= date_from.isoformat()]
            if date_to:
                filtered = [f for f in filtered if f.date <= date_to.isoformat()]
            if user_id:
                filtered = [f for f in filtered if f.user_id == user_id]
            if club_id:
                filtered = [f for f in filtered if f.club_id == club_id]
            return filtered[:limit]

        api = self._get_flight_api()
        params = {"limit": limit, "country_id_in": "NZ", "skip": offset}
        if date_from:
            params["scoring_date_start"] = date_from
        if date_to:
            params["scoring_date_end"] = date_to
        if user_id:
            params["user_id_in"] = str(user_id)
        if club_id:
            params["club_id_in"] = str(club_id)

        url = f"{self.host}/v1/flight"
        headers = {"User-Agent": DEFAULT_USER_AGENT}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"

        try:
            response = requests.get(url, params=params, headers=headers, timeout=30)
            response.raise_for_status()
            flights_data = response.json()
            if isinstance(flights_data, list):
                flights = []
                for f in flights_data:
                    airport_data = f.get("takeoff_airport", {})
                    bbox = f.get("bbox", [])
                    lat = bbox[1] if len(bbox) > 1 else 0.0
                    lon = bbox[0] if len(bbox) > 0 else 0.0
                    airport = APIAirport(
                        id=airport_data.get("id", 0),
                        name=airport_data.get("name", "Unknown"),
                        latitude=lat,
                        longitude=lon,
                    ) if airport_data else None
                    contest = f.get("contest", {})
                    club_data = f.get("club", {})
                    flight = APIFlight(
                        id=f.get("id", 0),
                        user_id=f.get("user", {}).get("id", 0),
                        user_name=f.get("user", {}).get("name", ""),
                        date=f.get("scoring_date", ""),
                        points=contest.get("points", 0.0),
                        distance=contest.get("distance", 0.0),
                        airport=airport,
                        club_id=club_data.get("id") if club_data else None,
                    )
                    flights.append(flight)
                return flights
            raise APIError(f"Unexpected response format: {type(flights_data)}")
        except requests.RequestException as e:
            raise APIError(f"Failed to fetch flights: {e}")

    def get_all_flights(
        self,
        date_from: date | None = None,
        date_to: date | None = None,
        user_id: int | None = None,
        club_id: int | None = None,
    ) -> Iterator:
        """Fetch all flights, handling pagination."""
        if self._mock_mode:
            yield from self.get_flights(date_from, date_to, user_id, club_id, limit=1000)
            return

        limit = 100
        while True:
            flights = self.get_flights(
                date_from=date_from,
                date_to=date_to,
                user_id=user_id,
                club_id=club_id,
                limit=limit,
            )
            if not flights:
                break
            yield from flights
            if len(flights) < limit:
                break

    def get_user(self, user_id: int) -> User:
        """Get user by ID."""
        if self._mock_mode:
            users = self._mock_data.get("users", [])
            for u in users:
                if u.id == user_id:
                    return u
            raise APIError(f"Mock user {user_id} not found")

        api = self._get_user_api()
        try:
            return api.get_user_v1_user_id_get(id=user_id)
        except ApiException as e:
            raise APIError(f"Failed to fetch user {user_id}: {e}")

    def search_users(self, query: str, limit: int = 20) -> list[User]:
        """Search for users by name or club."""
        if self._mock_mode:
            users = self._mock_data.get("users", [])
            return [u for u in users if query.lower() in u.name.lower()][:limit]

        api = self._get_user_api()
        try:
            return api.search_users_v1_user_search_get(query=query, limit=limit)
        except ApiException as e:
            raise APIError(f"Failed to search users: {e}")

    def get_club(self, club_id: int) -> Club:
        """Get club by ID."""
        if self._mock_mode:
            clubs = self._mock_data.get("clubs", [])
            for c in clubs:
                if c.id == club_id:
                    return c
            raise APIError(f"Mock club {club_id} not found")

        api = self._get_club_api()
        try:
            return api.get_club_v1_club_id_get(id=club_id)
        except ApiException as e:
            raise APIError(f"Failed to fetch club {club_id}: {e}")

    def search_clubs(self, query: str, limit: int = 20) -> list[Club]:
        """Search for clubs."""
        if self._mock_mode:
            clubs = self._mock_data.get("clubs", [])
            return [c for c in clubs if query.lower() in c.name.lower()][:limit]

        api = self._get_club_api()
        try:
            return api.search_clubs_v1_club_search_get(query=query, limit=limit)
        except ApiException as e:
            raise APIError(f"Failed to search clubs: {e}")