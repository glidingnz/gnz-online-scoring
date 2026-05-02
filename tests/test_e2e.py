"""End-to-end tests for the full workflow."""

from pathlib import Path
import tempfile

from src.weglide_client.config import load_config
from src.weglide_client.api_client import WeGlideClient
from src.weglide_client.island import Flight, Airport, apply_island_discount


MOCK_FLIGHTS = [
    Flight(1, 100, "2024-10-15", 500.0, airport=Airport(1, "Auckland", -36.8, 174.7)),
    Flight(2, 100, "2024-10-16", 300.0, airport=Airport(2, "Queenstown", -45.0, 168.7)),
    Flight(3, 100, "2024-10-17", 700.0, airport=Airport(3, "Auckland", -37.0, 174.7)),
    Flight(4, 200, "2024-10-20", 450.0, airport=Airport(4, "Queenstown", -45.0, 168.7)),
    Flight(5, 200, "2024-10-21", 600.0, airport=Airport(5, "Wellington", -41.3, 174.8)),
    Flight(6, 200, "2024-10-22", 200.0, airport=Airport(6, "Auckland", -36.9, 174.8)),
]


class TestEndToEnd:
    def test_full_workflow_with_mock_client(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            config_path.write_text("""
season:
  start_date: "2024-10-01"
  end_date: "2025-03-31"
island_assignment:
  100: "north"
  200: "south"
""")

            config = load_config(config_path)

            client = WeGlideClient()
            client.enable_mock({"flights": MOCK_FLIGHTS})

            with client:
                flights = list(client.get_all_flights(
                    date_from=config.season.start_date,
                    date_to=config.season.end_date,
                ))

            assert len(flights) == 6

            result = apply_island_discount(flights, config.island_assignment)

            assert len(result[100]) == 2
            assert result[100][0].points == 700.0
            assert result[100][1].points == 500.0

            assert len(result[200]) == 2
            assert result[200][0].points == 600.0
            assert result[200][1].points == 450.0

    def test_workflow_filters_wrong_island_flights(self):
        flights = [
            Flight(1, 100, "2024-10-15", 500.0, airport=Airport(1, "Auckland", -36.8, 174.7)),
            Flight(2, 100, "2024-10-16", 300.0, airport=Airport(2, "Queenstown", -45.0, 168.7)),
        ]
        pilot_map = {100: "north"}

        result = apply_island_discount(flights, pilot_map)

        assert len(result[100]) == 1
        assert result[100][0].id == 1

    def test_workflow_sorts_by_points(self):
        flights = [
            Flight(1, 100, "2024-10-15", 100.0, airport=Airport(1, "Auckland", -36.8, 174.7)),
            Flight(2, 100, "2024-10-16", 500.0, airport=Airport(2, "Auckland", -37.0, 174.7)),
            Flight(3, 100, "2024-10-17", 300.0, airport=Airport(3, "Auckland", -36.5, 174.7)),
        ]
        pilot_map = {100: "north"}

        result = apply_island_discount(flights, pilot_map)

        assert result[100][0].points == 500.0
        assert result[100][1].points == 300.0
        assert result[100][2].points == 100.0