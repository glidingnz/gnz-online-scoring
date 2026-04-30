# Implementation Status

## Current State: Complete ✓

### Source Code
- `app/` - Main application code
  - `config.py` - Configuration loading
  - `api_client.py` - WeGlide API wrapper with Chrome user-agent
  - `polygons.py` - Polygon-based island detection
  - `main.py` - CLI entry point and run_season function
  - `gui.py` - Tkinter GUI viewer
  - `island.py` - Island detection utilities

### Features Implemented

1. **Data Download**
   - CLI mode: Downloads flights from WeGlide API with date filtering
   - GUI mode: Button to trigger download with real-time output
   - Pagination support (fetches all flights within date range)

2. **Island Detection**
   - Polygon-based detection using convex polygons
   - Uses actual airport coordinates from WeGlide API
   - North Island: 5 vertices, South Island: 4 vertices

3. **Data Processing**
   - Groups flights by pilot and island
   - Each pilot gets top 5 flights per island (sorted by points)
   - Season dates stored in JSON files

4. **GUI Viewer**
   - Pilot list sorted by total points (descending)
   - Island selector (North/South)
   - Date selectors with validation
   - Flight details panel (5 flights per pilot)
   - OpenStreetMap integration showing flight locations
   - Preloaded maps for faster UX
   - Scrollable output log during download

5. **Build System**
   - PyInstaller-based executable
   - Single `release/gnz-online-scoring.exe`

### Output Files

| File | Description |
|------|-------------|
| `north_island.json` | North Island pilots with flights |
| `south_island.json` | South Island pilots with flights |
| `north_island.csv` | North Island rankings |
| `south_island.csv` | South Island rankings |
| `unmapped.json` | Flights not in polygons |
| `errors.txt` | Unmapped flight list |
| `log.txt` | Run summary |

### Build

```bash
python build.py
# Output: release/gnz-online-scoring.exe
```

### Usage

```bash
# Download data
python main.py --cli --start-date 2024-10-01 --end-date 2025-03-31

# View data
python main.py
```

Last updated: 2026-05-01