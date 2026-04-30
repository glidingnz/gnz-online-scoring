# WeGlide NZ Client

Python client for extracting and analyzing New Zealand glider flights from WeGlide API.

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

## Configuration

Edit `config.yaml` to set the season date range:

```yaml
season:
  start_date: "2024-10-01"
  end_date: "2025-03-31"

auth:
  username: ""
  password: ""
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

Flights are grouped by island based on takeoff airport latitude:
- **North Island**: latitude > -41°
- **South Island**: latitude < -41°

Each pilot can have up to 5 flights per island, sorted by points (descending).

## Current Data

The WeGlide database contains 7,782 NZ flights:
- North Island: 484 flights from 129 pilots
- South Island: 918 flights from 267 pilots

## Testing

```bash
python -m pytest tests/ -v
```

## Requirements

- Python 3.13+
- requests
- pydantic

Install dependencies:
```bash
pip install -e .
```