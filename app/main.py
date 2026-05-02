"""CLI entrypoint for WeGlide NZ client."""

import argparse
import csv
import json
import sys
import os
from pathlib import Path
from collections import defaultdict
from datetime import date

# Add path
_app_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _app_path)
sys.path.insert(0, os.path.join(_app_path, 'app'))

from config import Config
from api_client import WeGlideClient
from polygons import get_island_from_polygon
from selection import select_top_flights


MAX_FLIGHTS_PER_PILOT_ISLAND = 5


def get_island(lat: float, lon: float) -> str | None:
    """Determine island from polygon boundaries."""
    return get_island_from_polygon(lat, lon)


def run_season(config, mock: bool = False, output_dir: Path | None = None):
    """Run the season analysis."""
    print(f"Season: {config.season.start_date} to {config.season.end_date}")

    if mock:
        print("Mock mode not supported for this operation")
        return

    client = WeGlideClient(
        username=config.auth.username,
        password=config.auth.password,
    )

    print("Fetching all NZ flights between the selected dates...")
    all_flights = []
    page = 0
    while True:
        flights = client.get_flights(
            limit=100,
            offset=page * 100,
            date_from=config.season.start_date,
            date_to=config.season.end_date,
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

    for pilot_id, islands in pilot_flights.items():
        for island in ["north", "south"]:
            pilot_flights[pilot_id][island] = select_top_flights(pilot_flights[pilot_id][island], MAX_FLIGHTS_PER_PILOT_ISLAND)

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
                "valid": flight.valid,
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
                "valid": flight.valid,
                "origin": flight.airport.name if flight.airport else "Unknown",
                "latitude": flight.airport.latitude if flight.airport else 0,
                "longitude": flight.airport.longitude if flight.airport else 0,
            })

    if output_dir is None:
        output_dir = Path("./output")
    output_dir.mkdir(exist_ok=True)

    north_json = output_dir / "north_island.json"
    south_json = output_dir / "south_island.json"
    north_csv = output_dir / "north_island_all.csv"
    south_csv = output_dir / "south_island_all.csv"

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
                    "valid": f["valid"],
                    "origin": f["origin"],
                    "latitude": f["latitude"],
                    "longitude": f["longitude"],
                }
                for f in flights
            ]
        }

    season = {"start": str(config.season.start_date), "end": str(config.season.end_date)}

    with open(north_json, "w") as f:
        json.dump([{"season": season}] + [pilot_to_json(pid, flights) for pid, flights in sorted(north_by_pilot.items())], f, indent=2)
    print(f"Written {north_json}")

    with open(south_json, "w") as f:
        json.dump([{"season": season}] + [pilot_to_json(pid, flights) for pid, flights in sorted(south_by_pilot.items())], f, indent=2)
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

    def write_csv(csv_path: Path, data: list[dict], include_invalid: bool = True):
        """Write CSV file. If include_invalid is False, only valid flights."""
        if include_invalid:
            filtered = data
        else:
            filtered = [r for r in data if r.get("valid", True)]
        
        if filtered:
            pilot_data = defaultdict(lambda: {"points": [], "valid": []})
            for row in filtered:
                pid = row["pilot_id"]
                pilot_data[pid]["points"].append(row["points"])
                pilot_data[pid]["valid"].append(row.get("valid", True))
            
            with open(csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                if include_invalid:
                    writer.writerow(["pilot_id", "name", "Flight 1", "Flight 2", "Flight 3", "Flight 4", "Flight 5", "total", "notes"])
                else:
                    writer.writerow(["pilot_id", "name", "Flight 1", "Flight 2", "Flight 3", "Flight 4", "Flight 5", "total"])
                for pilot_id in sorted(pilot_data.keys()):
                    pd = pilot_data[pilot_id]
                    name = pilot_names.get(pilot_id, f"Pilot {pilot_id}")
                    
                    # Get first 5 flights
                    points = pd["points"][:5]
                    valid = pd["valid"][:5]
                    
                    # Pad to 5 flights
                    while len(points) < 5:
                        points.append("")
                        valid.append(True)
                    
                    row = [pilot_id, name] + points
                    total = sum(p for p in points if isinstance(p, (int, float)) and p)
                    row.append(f"{total:.2f}")
                    
                    if include_invalid:
                        # Find which flights are invalid
                        invalid_indices = [i+1 for i, v in enumerate(valid) if not v]
                        if invalid_indices:
                            flight_word = "Flight" if len(invalid_indices) == 1 else "Flights"
                            notes = f"{flight_word} " + "; ".join(str(i) for i in invalid_indices) + " invalid!"
                        else:
                            notes = ""
                        row.append(notes)
                    
                    writer.writerow(row)
            return len(filtered)
        return 0

    north_csv = output_dir / "north_island_all.csv"
    south_csv = output_dir / "south_island_all.csv"

    write_csv(north_csv, north_data, include_invalid=True)
    print(f"Written {north_csv}")
    write_csv(north_csv.parent / "north_island_valid.csv", north_data, include_invalid=False)
    print(f"Written {north_csv.parent / 'north_island_valid.csv'}")
    write_csv(south_csv, south_data, include_invalid=True)
    print(f"Written {south_csv}")
    write_csv(south_csv.parent / "south_island_valid.csv", south_data, include_invalid=False)
    print(f"Written {south_csv.parent / 'south_island_valid.csv'}")

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
        f.write(f"  - {north_csv.name} (all flights)\n")
        f.write(f"  - north_island_valid.csv (valid only)\n")
        f.write(f"  - {south_csv.name} (all flights)\n")
        f.write(f"  - south_island_valid.csv (valid only)\n")
        f.write(f"  - {errors_file.name}\n")
        f.write(f"  - {log_file.name}\n")
    print(f"Written {log_file}")


def main(args=None):
    parser = argparse.ArgumentParser(description="GNZ Online Scoring")
    parser.add_argument("--cli", action="store_true", help="Run in CLI mode (no GUI)")
    parser.add_argument("--mock", action="store_true", help="Use mock data (CLI mode)")
    parser.add_argument("--output-dir", type=Path, help="Output directory (CLI mode)")
    parser.add_argument("--start-date", help="Season start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", help="Season end date (YYYY-MM-DD)")
    args = parser.parse_args(args)

    if args.cli:
        from datetime import date
        from config import Config, SeasonConfig, AuthConfig

        if not args.start_date or not args.end_date:
            print("Error: --start-date and --end-date are required in CLI mode", file=sys.stderr)
            sys.exit(1)

        config = Config(
            season=SeasonConfig(
                start_date=date.fromisoformat(args.start_date),
                end_date=date.fromisoformat(args.end_date),
            ),
            auth=AuthConfig(),
        )
        run_season(config, mock=args.mock, output_dir=args.output_dir)
    else:
        from gui import main as gui_main
        gui_main()


def _main():
    pass


if __name__ == "__main__":
    main()