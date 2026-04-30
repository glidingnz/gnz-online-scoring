# Implementation Status

## Current State: Complete

### Completed ✓
- pyproject.toml - dependencies configured
- config.yaml - simplified config (season dates only)
- `src/weglide_client/` - main package (renamed from weglide_nz)
  - `__init__.py` - package init
  - `config.py` - config loading
  - `api_client.py` - API wrapper with Chrome user-agent
  - `polygons.py` - polygon-based island detection
  - `main.py` - CLI entrypoint
- tests/ - 25 tests passing

### Features
- Fetches all NZ flights from WeGlide API
- Groups flights by island using convex polygon boundaries
- Uses actual airport coordinates from WeGlide API (not flight bbox)
- For each pilot on each island: top 5 flights by points
- Unmapped flights reported in errors.txt and unmapped.json

### Output Files
- `output/north_island.json` / `output/north_island.csv`
- `output/south_island.json` / `output/south_island.csv`
- `output/unmapped.json` - flights not in either polygon
- `output/errors.txt` - list of unmapped flights
- `output/log.txt` - run summary

### Build System
- `build.py` - builds the executable
- `release/` - output folder with exe + config + README
- PyInstaller for cross-platform builds

### Current Results
- North Island: 584 flights from 159 pilots
- South Island: 807 flights from 238 pilots
- Total: 7,782 NZ flights
- Unmapped: 0 flights (polygon detection working)

## Configuration

```yaml
season:
  start_date: "2024-10-01"
  end_date: "2025-03-31"
```

## Usage

```bash
# Run with real API
python -m src.weglide_nz.main

# Output to custom directory
python -m src.weglide_nz.main --output-dir ./output
```

## Build

```bash
python build.py
# Output: release/ folder
```

Last updated: 2026-04-30