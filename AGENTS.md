# WeGlide Client

Python client for extracting and analyzing New Zealand glider flights from WeGlide API.

## API Reference

- **API Docs**: https://docs.weglide.org/creators/developers.html
- **Swagger**: https://api.weglide.org/docs
- **Python Client**: `pip install weglide-client` (see https://github.com/develmusa/WeGlide-Python-Client)

## Configuration

Create `config.yaml` with:
```yaml
season:
  start_date: "2024-10-01"  # Season start (ISO format)
  end_date: "2025-03-31"    # Season end (ISO format)
```

Note: Credentials are optional - the public API works without authentication.

## Key API Endpoints

- **Flights**: `FlightApi.get_flights_v1_flight_get()` - supports filtering by date range, user, club
- **Users**: `UserApi.get_user_v1_user_id_get(id=...)` or search
- **Clubs**: `ClubApi` - needed to determine pilot club affiliation and island

## Implementation Notes

1. **Filtering by date**: Pass `date_from` and `date_to` params to flight endpoint
2. **Country filtering**: Search for users/clubs in New Zealand (country code NZ or search "New Zealand")
3. **Flight points**: Each flight has a `points` field for scoring
4. **Airport/location**: Each flight has `airport` or takeoff location - use this to determine which island the flight is on

## Island Detection Logic

Uses convex polygons defined in `src/weglide_client/polygons.py`:
- North Island polygon: 5 vertices
- South Island polygon: 4 vertices

Coordinates are fetched from WeGlide's airport API (not flight bbox, which is the flight path).

For each flight:
1. Get airport ID from flight
2. Fetch airport coordinates from `/v1/airport/{id}`
3. Check if coordinates fall within either polygon
4. If neither, log to errors.txt and unmapped.json

Each pilot gets top 5 flights per island, sorted by points (descending).

## Running

```bash
# Run with real API
python -m src.weglide_client.main

# Specify output directory
python -m src.weglide_client.main --output-dir ./output

# Run with mock data for testing
python -m src.weglide_client.main --mock
```

## Build Executable

```bash
python build.py
# Output: release/ folder with weglide-nz.exe + config.yaml
```

## Important Notes

- Uses Chrome user-agent header to bypass 403 blocking
- Public API access works without credentials
- Uses direct HTTP requests (not weglide-client) for better control
- Fetches actual airport coordinates from `/v1/airport/{id}` endpoint
- Tests: 25 tests passing. Run with `python -m pytest tests/`
- Status: See STATUS.md and PLAN.md for details