# WeGlide Client - Developer Notes

Python client for extracting and analyzing New Zealand glider flights from WeGlide API.

## API Reference

- **API Docs**: https://docs.weglide.org/creators/developers.html
- **Swagger**: https://api.weglide.org/docs
- **Python Client**: `pip install weglide-client` (see https://github.com/develmusa/WeGlide-Python-Client)

## Implementation Notes

### Data Flow

1. CLI or GUI downloads flights from WeGlide API
2. For each flight, fetch airport coordinates from `/v1/airport/{id}`
3. Determine island using polygon detection
4. Group flights by pilot and island
5. For each pilot on each island: keep top 5 flights by points

### Key Implementation Details

- **Filtering**: Pass `date_from` and `date_to` params to flight endpoint
- **Country**: Filter for NZ (New Zealand) flights
- **Airport location**: Use actual takeoff airport coordinates, not flight bbox
- **Points**: Each flight has a `points` field for scoring

### Island Detection

Uses convex polygons defined in `app/polygons.py`:
- North Island polygon: 5 vertices
- South Island polygon: 4 vertices

Coordinates are fetched from WeGlide's airport API.

## Running

```bash
# Download data
python main.py --cli --start-date 2024-10-01 --end-date 2025-03-31

# View data
python main.py

# Build executable
python build.py
```

## Testing

```bash
python -m pytest tests/ -v
```

## Important Notes

- Uses Chrome user-agent header to bypass 403 blocking
- Public API access works without credentials
- Uses direct HTTP requests (not weglide-client package) for better control
- Fetches actual airport coordinates from `/v1/airport/{id}` endpoint

## Project Structure

```
app/
  config.py     - Config loading
  api_client.py - WeGlide API wrapper
  polygons.py  - Island polygon definitions
  main.py       - CLI entry point (run_season function)
  gui.py        - Tkinter GUI viewer
  island.py     - Island detection utilities

main.py         - Wrapper entry point (for PyInstaller)
build.py        - Build script
```