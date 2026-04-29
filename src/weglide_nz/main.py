"""CLI entrypoint for WeGlide NZ client."""

import argparse
import json
import sys
from pathlib import Path

from src.weglide_nz.config import load_config
from src.weglide_nz.api_client import WeGlideClient
from src.weglide_nz.island import Flight, Airport, apply_island_discount


def create_mock_flight(flight_id: int, user_id: int, date: str, points: float, lat: float, lon: float, airport_name: str):
    """Helper to create mock flights."""
    return Flight(
        id=flight_id,
        user_id=user_id,
        date=date,
        points=points,
        airport=Airport(id=flight_id, name=airport_name, latitude=lat, longitude=lon),
    )


MOCK_FLIGHTS = [
    create_mock_flight(1, 100, "2024-10-15", 500.0, -36.8, 174.7, "Auckland"),
    create_mock_flight(2, 100, "2024-10-16", 300.0, -45.0, 168.7, "Queenstown"),
    create_mock_flight(3, 100, "2024-10-17", 700.0, -37.0, 174.7, "Auckland"),
    create_mock_flight(4, 200, "2024-10-20", 450.0, -45.0, 168.7, "Queenstown"),
    create_mock_flight(5, 200, "2024-10-21", 600.0, -41.3, 174.8, "Wellington"),
    create_mock_flight(6, 200, "2024-10-22", 200.0, -36.9, 174.8, "Auckland"),
    create_mock_flight(7, 300, "2024-11-01", 800.0, -45.0, 168.7, "Queenstown"),
    create_mock_flight(8, 300, "2024-11-02", 100.0, -36.8, 174.7, "Auckland"),
]


def run_season(config_path: Path, mock: bool = False):
    """Run the season analysis."""
    config = load_config(config_path)
    print(f"Season: {config.season.start_date} to {config.season.end_date}")

    island_assignment = config.island_assignment
    if not island_assignment:
        print("No island assignments configured")
        return

    if mock:
        flights = MOCK_FLIGHTS
        print(f"Using mock data: {len(flights)} flights")
    else:
        client = WeGlideClient(
            username=config.auth.username,
            password=config.auth.password,
        )
        with client:
            print("Fetching flights from API...")
            flights = list(client.get_all_flights(
                date_from=config.season.start_date,
                date_to=config.season.end_date,
            ))
            print(f"Fetched {len(flights)} flights")

    result = apply_island_discount(flights, island_assignment)

    print("\n=== Results ===")
    for pilot_id, pilot_flights in result.items():
        print(f"\nPilot {pilot_id}: {len(pilot_flights)} valid flights")
        for f in pilot_flights:
            island = "N" if f.airport and f.airport.latitude > -41 else "S"
            print(f"  - {f.date}: {f.points}pts ({f.airport.name} [{island}])")

    return result


def main():
    parser = argparse.ArgumentParser(description="WeGlide NZ Season Analysis")
    parser.add_argument("--config", default="config.yaml", help="Config file path")
    parser.add_argument("--mock", action="store_true", help="Use mock data")
    parser.add_argument("--output", help="Output JSON file")
    args = parser.parse_args()

    config_path = Path(args.config)
    if not config_path.exists():
        print(f"Config file not found: {config_path}", file=sys.stderr)
        sys.exit(1)

    result = run_season(config_path, mock=args.mock)

    if args.output and result:
        with open(args.output, "w") as f:
            json.dump(
                {pid: [{"id": f.id, "date": f.date, "points": f.points, "airport": f.airport.name} for f in flights]
                 for pid, flights in result.items()},
                f, indent=2)
            print(f"Results written to {args.output}")


if __name__ == "__main__":
    main()