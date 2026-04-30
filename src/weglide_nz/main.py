"""CLI entrypoint for WeGlide NZ client."""

import argparse
import csv
import json
import sys
from pathlib import Path
from collections import defaultdict
from datetime import date

from src.weglide_nz.config import load_config
from src.weglide_nz.api_client import WeGlideClient
from src.weglide_nz.polygons import get_island_from_polygon


MAX_FLIGHTS_PER_PILOT_ISLAND = 5


def get_island(lat: float, lon: float) -> str | None:
    """Determine island from polygon boundaries."""
    return get_island_from_polygon(lat, lon)


def run_season(config_path: Path, mock: bool = False, output_dir: Path | None = None):
    """Run the season analysis."""
    config = load_config(config_path)
    print(f"Season: {config.season.start_date} to {config.season.end_date}")

    if mock:
        print("Mock mode not supported for this operation")
        return

    client = WeGlideClient(
        username=config.auth.username,
        password=config.auth.password,
    )

    print("Fetching all NZ flights...")
    all_flights = []
    page = 0
    while True:
        flights = client.get_flights(
            limit=100,
            offset=page * 100,
        )
        if not flights:
            break
        all_flights.extend(flights)
        print(f"  Fetched page {page + 1}, total: {len(all_flights)}")
        page += 1
        if len(flights) < 100:
            print(f"  Reached end of data at page {page + 1}")
            break
        if page > 100:
            print("  Stopping after 100 pages")
            break

    print(f"Total flights: {len(all_flights)}")

    pilot_flights = defaultdict(lambda: {"north": [], "south": []})
    pilot_names = {}
    unmapped_flights = []

    for flight in all_flights:
        if not flight.airport or flight.airport.latitude == 0:
            continue
        island = get_island(flight.airport.latitude, flight.airport.longitude)
        if island is None:
            unmapped_flights.append({
                "flight_id": flight.id,
                "pilot_id": flight.user_id,
                "pilot_name": flight.user_name,
                "date": flight.date,
                "latitude": flight.airport.latitude,
                "longitude": flight.airport.longitude,
                "airport": flight.airport.name,
            })
            continue
        pilot_names[flight.user_id] = flight.user_name
        pilot_flights[flight.user_id][island].append(flight)

    for pilot_id in pilot_flights:
        for island in ["north", "south"]:
            pilot_flights[pilot_id][island].sort(key=lambda f: f.points, reverse=True)
            pilot_flights[pilot_id][island] = pilot_flights[pilot_id][island][:MAX_FLIGHTS_PER_PILOT_ISLAND]

    north_data = []
    south_data = []
    unmapped_data = []

    for pilot_id, islands in pilot_flights.items():
        for flight in islands["north"]:
            north_data.append({
                "pilot_id": pilot_id,
                "pilot_name": pilot_names.get(pilot_id, ""),
                "flight_id": flight.id,
                "date": flight.date,
                "points": flight.points,
                "distance": flight.distance,
                "origin": flight.airport.name if flight.airport else "Unknown",
                "latitude": flight.airport.latitude if flight.airport else 0,
                "longitude": flight.airport.longitude if flight.airport else 0,
            })
        for flight in islands["south"]:
            south_data.append({
                "pilot_id": pilot_id,
                "pilot_name": pilot_names.get(pilot_id, ""),
                "flight_id": flight.id,
                "date": flight.date,
                "points": flight.points,
                "distance": flight.distance,
                "origin": flight.airport.name if flight.airport else "Unknown",
                "latitude": flight.airport.latitude if flight.airport else 0,
                "longitude": flight.airport.longitude if flight.airport else 0,
            })

    if output_dir is None:
        output_dir = Path("./output")
    output_dir.mkdir(exist_ok=True)

    north_json = output_dir / "north_island.json"
    south_json = output_dir / "south_island.json"
    north_csv = output_dir / "north_island.csv"
    south_csv = output_dir / "south_island.csv"

    north_by_pilot = defaultdict(list)
    for row in north_data:
        north_by_pilot[row["pilot_id"]].append(row)
    south_by_pilot = defaultdict(list)
    for row in south_data:
        south_by_pilot[row["pilot_id"]].append(row)

    def pilot_to_json(pilot_id, flights):
        total = sum(f["points"] for f in flights)
        return {
            "pilot_id": pilot_id,
            "pilot_name": flights[0]["pilot_name"] if flights else "",
            "total_points": round(total, 2),
            "flights": [
                {
                    "flight_id": f["flight_id"],
                    "date": f["date"],
                    "points": f["points"],
                    "distance": f["distance"],
                    "origin": f["origin"],
                    "latitude": f["latitude"],
                    "longitude": f["longitude"],
                }
                for f in flights
            ]
        }

    with open(north_json, "w") as f:
        json.dump([pilot_to_json(pid, flights) for pid, flights in sorted(north_by_pilot.items())], f, indent=2)
    print(f"Written {north_json}")

    with open(south_json, "w") as f:
        json.dump([pilot_to_json(pid, flights) for pid, flights in sorted(south_by_pilot.items())], f, indent=2)
    print(f"Written {south_json}")

    unmapped_json = output_dir / "unmapped.json"
    with open(unmapped_json, "w") as f:
        json.dump(unmapped_flights, f, indent=2)
    print(f"Written {unmapped_json} ({len(unmapped_flights)} flights)")

    errors_file = output_dir / "errors.txt"
    with open(errors_file, "w", encoding="utf-8") as f:
        f.write("Flights not in North or South Island polygons:\n")
        f.write("=" * 60 + "\n")
        for uf in unmapped_flights:
            f.write(f"Flight {uf['flight_id']}: {uf['airport']} ({uf['latitude']:.4f}, {uf['longitude']:.4f})\n")
            f.write(f"  Pilot: {uf['pilot_name']} ({uf['pilot_id']}), Date: {uf['date']}\n")
    print(f"Written {errors_file}")

    for csv_file, data in [(north_csv, north_data), (south_csv, south_data)]:
        if data:
            pilot_rows = defaultdict(list)
            for row in data:
                pilot_rows[row["pilot_id"]].append(row["points"])
            with open(csv_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["pilot_id", "name", "Flight 1", "Flight 2", "Flight 3", "Flight 4", "Flight 5", "total"])
                for pilot_id, points in sorted(pilot_rows.items()):
                    name = pilot_names.get(pilot_id, f"Pilot {pilot_id}")
                    row = [pilot_id, name] + points[:5]
                    total = sum(p for p in points[:5] if p)
                    row.append(f"{total:.2f}")
                    writer.writerow(row)
        print(f"Written {csv_file}")

    print(f"\nSummary:")
    print(f"  North Island: {len(north_data)} flights from {len(set(d['pilot_id'] for d in north_data))} pilots")
    print(f"  South Island: {len(south_data)} flights from {len(set(d['pilot_id'] for d in south_data))} pilots")
    print(f"  Unmapped: {len(unmapped_flights)} flights")

    log_file = output_dir / "log.txt"
    with open(log_file, "w", encoding="utf-8") as f:
        f.write("GNZ Online Scoring - Run Summary\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Season: {config.season.start_date} to {config.season.end_date}\n")
        f.write(f"Total flights processed: {len(all_flights)}\n\n")
        f.write("Island Breakdown:\n")
        f.write(f"  North Island: {len(north_data)} flights from {len(set(d['pilot_id'] for d in north_data))} pilots\n")
        f.write(f"  South Island: {len(south_data)} flights from {len(set(d['pilot_id'] for d in south_data))} pilots\n")
        f.write(f"  Unmapped (not in polygons): {len(unmapped_flights)} flights\n\n")
        f.write("Output Files:\n")
        f.write(f"  - {north_json.name}\n")
        f.write(f"  - {south_json.name}\n")
        f.write(f"  - {unmapped_json.name}\n")
        f.write(f"  - {north_csv.name}\n")
        f.write(f"  - {south_csv.name}\n")
        f.write(f"  - {errors_file.name}\n")
        f.write(f"  - {log_file.name}\n")
    print(f"Written {log_file}")


def main():
    parser = argparse.ArgumentParser(description="WeGlide NZ Season Analysis")
    parser.add_argument("--config", default="config.yaml", help="Config file path")
    parser.add_argument("--mock", action="store_true", help="Use mock data")
    parser.add_argument("--output-dir", type=Path, help="Output directory for JSON/CSV files")
    args = parser.parse_args()

    config_path = Path(args.config)
    if not config_path.exists():
        print(f"Config file not found: {config_path}", file=sys.stderr)
        sys.exit(1)

    run_season(config_path, mock=args.mock, output_dir=args.output_dir)


if __name__ == "__main__":
    main()