"""Tests for island detection logic."""

import pytest
from src.weglide_nz.island import (
    get_island_from_latitude,
    detect_flight_island,
    apply_island_discount,
    Flight,
    Airport,
    LATITUDE_THRESHOLD,
)


class TestGetIslandFromLatitude:
    def test_north_island_typical_latitudes(self):
        assert get_island_from_latitude(-36.8) == "north"
        assert get_island_from_latitude(-38.0) == "north"
        assert get_island_from_latitude(-40.9) == "north"

    def test_south_island_typical_latitudes(self):
        assert get_island_from_latitude(-41.1) == "south"
        assert get_island_from_latitude(-45.0) == "south"
        assert get_island_from_latitude(-50.0) == "south"

    def test_threshold_boundary(self):
        assert get_island_from_latitude(-40.99) == "north"

    def test_exactly_threshold(self):
        assert get_island_from_latitude(-40.999) == "north"
        assert get_island_from_latitude(-41.001) == "south"


class TestDetectFlightIsland:
    def test_flight_with_valid_airport(self):
        flight = Flight(1, 123, "2024-10-15", 500.0, airport=Airport(1, "Auckland", -36.8, 174.7))
        assert detect_flight_island(flight) == "north"

    def test_flight_with_south_island_airport(self):
        flight = Flight(2, 123, "2024-10-15", 500.0, airport=Airport(2, "Queenstown", -45.0, 168.7))
        assert detect_flight_island(flight) == "south"

    def test_flight_without_airport(self):
        flight = Flight(3, 123, "2024-10-15", 500.0, airport=None)
        assert detect_flight_island(flight) is None


class TestApplyIslandDiscount:
    def test_pilot_with_valid_and_invalid_flights(self):
        flights = [
            Flight(1, 123, "2024-10-15", 500.0, airport=Airport(1, "Auckland", -36.8, 174.7)),
            Flight(2, 123, "2024-10-16", 600.0, airport=Airport(2, "Queenstown", -45.0, 168.7)),
            Flight(3, 123, "2024-10-17", 400.0, airport=Airport(3, "Auckland", -37.0, 174.7)),
        ]
        pilot_map = {123: "north"}
        result = apply_island_discount(flights, pilot_map)

        assert len(result[123]) == 2
        assert result[123][0].points == 500.0
        assert result[123][1].points == 400.0

    def test_flights_sorted_by_points_descending(self):
        flights = [
            Flight(1, 123, "2024-10-15", 100.0, airport=Airport(1, "Auckland", -36.8, 174.7)),
            Flight(2, 123, "2024-10-16", 500.0, airport=Airport(2, "Auckland", -37.0, 174.7)),
            Flight(3, 123, "2024-10-17", 300.0, airport=Airport(3, "Auckland", -36.5, 174.7)),
        ]
        pilot_map = {123: "north"}
        result = apply_island_discount(flights, pilot_map)

        assert result[123][0].points == 500.0
        assert result[123][1].points == 300.0
        assert result[123][2].points == 100.0

    def test_multiple_pilots(self):
        flights = [
            Flight(1, 100, "2024-10-15", 500.0, airport=Airport(1, "Auckland", -36.8, 174.7)),
            Flight(2, 200, "2024-10-16", 400.0, airport=Airport(2, "Queenstown", -45.0, 168.7)),
        ]
        pilot_map = {100: "north", 200: "south"}
        result = apply_island_discount(flights, pilot_map)

        assert len(result[100]) == 1
        assert len(result[200]) == 1

    def test_pilot_not_in_map(self):
        flights = [Flight(1, 123, "2024-10-15", 500.0, airport=Airport(1, "Auckland", -36.8, 174.7))]
        pilot_map = {999: "north"}
        result = apply_island_discount(flights, pilot_map)

        assert 123 not in result

    def test_south_island_pilot(self):
        flights = [
            Flight(1, 123, "2024-10-15", 500.0, airport=Airport(1, "Auckland", -36.8, 174.7)),
            Flight(2, 123, "2024-10-16", 600.0, airport=Airport(2, "Queenstown", -45.0, 168.7)),
        ]
        pilot_map = {123: "south"}
        result = apply_island_discount(flights, pilot_map)

        assert len(result[123]) == 1
        assert result[123][0].airport.name == "Queenstown"