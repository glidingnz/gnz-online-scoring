"""Island detection and filtering logic."""

from dataclasses import dataclass
from typing import Any


LATITUDE_THRESHOLD = -41.0


@dataclass
class Airport:
    """Represents an airport with location data."""
    id: int
    name: str
    latitude: float
    longitude: float


@dataclass
class Flight:
    """Represents a flight with location and points."""
    id: int
    user_id: int
    date: str
    points: float
    airport: Airport | None = None
    club_id: int | None = None


def get_island_from_latitude(latitude: float) -> str:
    """Determine island from airport latitude.

    North Island: latitude > -41.0 (e.g., -36.8° = Auckland)
    South Island: latitude < -41.0 (e.g., -45.0° = Queenstown)
    """
    if latitude > LATITUDE_THRESHOLD:
        return "north"
    return "south"


def detect_flight_island(flight: Flight) -> str | None:
    """Detect which island a flight took place on.

    Returns 'north', 'south', or None if airport data unavailable.
    """
    if flight.airport is None:
        return None
    return get_island_from_latitude(flight.airport.latitude)


def apply_island_discount(
    flights: list[Flight],
    pilot_island_map: dict[int, str],
) -> dict[int, list[Flight]]:
    """Apply island discount: filter out flights on wrong island.

    For each pilot:
    1. Get their assigned island from pilot_island_map
    2. Filter out flights where flight island != pilot island
    3. Sort remaining flights by points (descending)
    4. Return flights grouped by pilot, sorted by points

    Args:
        flights: List of all flights
        pilot_island_map: Mapping of pilot_id -> 'north' or 'south'

    Returns:
        Dict of pilot_id -> list of valid flights sorted by points descending
    """
    result: dict[int, list[Flight]] = {}

    for pilot_id, assigned_island in pilot_island_map.items():
        pilot_flights = [f for f in flights if f.user_id == pilot_id]

        valid_flights = []
        for flight in pilot_flights:
            flight_island = detect_flight_island(flight)
            if flight_island is None:
                continue
            if flight_island == assigned_island:
                valid_flights.append(flight)

        valid_flights.sort(key=lambda f: f.points, reverse=True)
        result[pilot_id] = valid_flights

    return result