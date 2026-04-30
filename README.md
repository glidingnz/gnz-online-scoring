# GNZ Online Scoring

Python application for extracting and analyzing New Zealand glider flights from the WeGlide API.

**Use cases:** Air NZ XC Award, Buckland Trophy

## Overview

This application downloads flight data from WeGlide and groups flights by island (North/South) using polygon boundaries. Each pilot's top 5 flights per island are ranked by points.

## Quick Start

### Using the executable (recommended)

```bash
# Download data (CLI mode)
release/gnz-online-scoring.exe --cli --start-date 2024-10-01 --end-date 2025-03-31

# View data (GUI mode)
release/gnz-online-scoring.exe
```

### Using Python

```bash
# Download data (CLI mode)
python main.py --cli --start-date 2024-10-01 --end-date 2025-03-31

# View data (GUI mode)
python main.py
```

## Workflow

1. **Download data** - Use CLI mode to fetch flights from WeGlide API
2. **View data** - Use GUI to explore pilot rankings and flight details with maps

## CLI Options

| Option | Description |
|--------|-------------|
| `--cli` | Run in CLI mode (download data) |
| `--start-date YYYY-MM-DD` | Season start date (required for download) |
| `--end-date YYYY-MM-DD` | Season end date (required for download) |
| `--output-dir PATH` | Output directory (default: `./output`) |

## Output Files

The application creates these files in the output directory:

| File | Description |
|------|-------------|
| `north_island.json` | North Island pilots with flight details |
| `south_island.json` | South Island pilots with flight details |
| `north_island.csv` | North Island summary (pilot rankings) |
| `south_island.csv` | South Island summary (pilot rankings) |
| `unmapped.json` | Flights not in either polygon |
| `errors.txt` | List of unmapped flights |
| `log.txt` | Run summary |

### JSON Format

```json
{
  "season": {"start": "2024-10-01", "end": "2025-03-31"},
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

### CSV Format

| pilot_id | name | Flight 1 | Flight 2 | Flight 3 | Flight 4 | Flight 5 | total |
|----------|------|----------|----------|----------|----------|----------|-------|
| 650 | Tim Bromhead | 621.51 | 588.15 | 555.3 | 536.53 | 535.99 | 2837.48 |

## Island Detection

Flights are grouped by island using convex polygon boundaries:

- **North Island**: 5-vertex polygon covering the northern region
- **South Island**: 4-vertex polygon covering the southern region

The detection uses actual airport coordinates fetched from WeGlide's airport API (not flight path bounding boxes).

Each pilot gets up to 5 flights per island, sorted by points (descending).

## GUI Features

- **Pilot list** - Sorted by total points (descending)
- **Island selector** - Switch between North/South island data
- **Flight details** - View top 5 flights per pilot with:
  - Flight info (date, points, distance, origin)
  - Map showing flight location (OpenStreetMap)
- **Date validation** - Warns if North/South files have different date ranges
- **Preloaded maps** - OSM tiles cached for faster viewing

## Building the Executable

### Prerequisites

```bash
pip install pyinstaller pyyaml pydantic requests pillow
```

### Build

```bash
python build.py
```

The executable is created in `release/gnz-online-scoring.exe`.

## Requirements

- Python 3.9+
- requests
- pydantic
- pyyaml
- Pillow (for map images)
- tkinter (included with Python)

## Files

- `app/` - Source code
- `build.py` - Build script
- `main.py` - Entry point
- `release/` - Built executable