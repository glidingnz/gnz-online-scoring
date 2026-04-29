"""WeGlide API client wrapper."""

import weglide_client
from weglide_client import Club, User
from weglide_client.api import club_api, flight_api, user_api, auth_api
from weglide_client.rest import ApiException
from dataclasses import dataclass, field
from datetime import date
from typing import Iterator, Any


DEFAULT_HOST = "https://api.weglide.org"


class APIError(Exception):
    """API error."""
    pass


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
            if not self.username or not self.password:
                raise APIError("Username and password required. Add them to config.yaml or use --mock for testing.")

            print(f"Authenticating as {self.username}...")
            self._token = self._authenticate()
            print("Authentication successful")

            configuration = weglide_client.Configuration(host=self.host)
            configuration.api_key = {"Authorization": self._token}
            configuration.api_key_prefix = {"Authorization": "Bearer"}
            self._client = weglide_client.ApiClient(configuration)
        return self

    def _authenticate(self) -> str:
        """Authenticate with username/password and return access token."""
        temp_config = weglide_client.Configuration(host=self.host)
        temp_client = weglide_client.ApiClient(temp_config)
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
        if self._client:
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
        params = {"limit": limit}
        if date_from:
            params["date_from"] = date_from.isoformat()
        if date_to:
            params["date_to"] = date_to.isoformat()
        if user_id:
            params["user_id"] = user_id
        if club_id:
            params["club_id"] = club_id

        try:
            return api.flightlist_v1_flight_get(**params)
        except ApiException as e:
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