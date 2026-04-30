# GNZ Online Scoring

Python client for extracting and analyzing New Zealand glider flights from WeGlide API.

Use cases:

- Air NZ XC Award
- Buckland Trophy

## Quick Start

```bash
# Run the script to fetch all NZ flights and generate output files
python -m src.weglide_nz.main
```

Output files will be created in `./output/`:
- `north_island.json` - Detailed flight data for North Island pilots
- `south_island.json` - Detailed flight data for South Island pilots
- `north_island.csv` - Summary CSV for North Island
- `south_island.csv` - Summary CSV for South Island
- `unmapped.json` - Flights not in either polygon
- `errors.txt` - List of unmapped flights
- `log.txt` - Run summary

## Configuration

Edit `config.yaml` to set the season date range:

```yaml
season:
  start_date: "2024-10-01"
  end_date: "2025-03-31"
```

Note: Credentials are optional - the script works without them using public API access.

## Output Format

### CSV
| pilot_id | name | Flight 1 | Flight 2 | Flight 3 | Flight 4 | Flight 5 | total |
|----------|------|----------|----------|----------|----------|----------|-------|
| 650 | Tim Bromhead | 621.51 | 588.15 | 555.3 | 536.53 | 535.99 | 2837.48 |

### JSON
```json
{
  "pilot_id": 650,
  "pilot_name": "Tim Bromhead",
  "total_points": 2837.48,
  "flights": [
    {
      "flight_id": 1062061,
      "date": "2025-03-30",
      "points": 621.51,
      "distance": 432.65,
      "origin": "Drury",
      "latitude": -36.8,
      "longitude": 174.7
    }
  ]
}
```

## Island Logic

Flights are grouped by island based on convex polygon boundaries defined in `polygons.py`:
- North Island: 5-vertex polygon
- South Island: 4-vertex polygon

Coordinates are fetched from WeGlide's airport API to determine actual takeoff location.

Each pilot can have up to 5 flights per island, sorted by points (descending).

## Current Data

The WeGlide database contains 7,782 NZ flights:
- North Island: 584 flights from 159 pilots
- South Island: 807 flights from 238 pilots
- Unmapped: 0 flights

## Testing

```bash
python -m pytest tests/ -v
```

## Requirements

- Python 3.9+
- requests
- pydantic
- pyyaml

Install dependencies:
```bash
pip install -e .
```

## Building Executable

### Prerequisites
```bash
pip install pyinstaller
```

### Build

```bash
python build.py
```

This creates a `release/` folder containing:
- `gnz-online-scoring.exe` - The executable
- `config.yaml` - Configuration file
- `README.md` - This file

To run the built executable:
```bash
cd release
./weglide-nz.exe
```

### Cross-compilation

- **Windows on Linux**: Use Wine with PyInstaller
- **Linux on Windows**: Use WSL with PyInstaller

The build script uses `build_output/` as a temp folder - this is cleaned on each build.