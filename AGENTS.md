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

auth:
  username: "your_weglide_email"
  password: "your_password"

island_assignment:
  # Pilot ID -> island mapping (north/south)
  # Example: {123: "north", 456: "south"}
  100: "north"
  200: "south"
```

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

- Get pilot's club from user profile
- Map club to North/South island (via config/external lookup)
- For each flight, check `airport.latitude` to determine flight location:
  - Latitude > ~41S = North Island
  - Latitude < ~41S = South Island
- Apply discount: remove flights where pilot's island != flight island, keeping highest-point flights first

## Running

```bash
# Run with real API (if IP is whitelisted)
python -m src.weglide_nz.main

# Run with mock data for testing
python -m src.weglide_nz.main --mock

# Output to JSON
python -m src.weglide_nz.main --mock --output results.json
```

## Important Notes

- **API blocking**: Non-residential/VPN IPs get 403 Forbidden. Contact info@weglide.org for API key.
- **Flight endpoint**: Use `flightlist_v1_flight_get` not `get_flights_v1_flight_get`
- **Authentication**: Uses OAuth2 password grant. Add credentials to config.yaml.
- **Mock mode**: `client.enable_mock(data)` for testing without API
- **Tests**: 25 tests passing. Run with `python -m pytest tests/`
- **Status**: See STATUS.md and PLAN.md for details