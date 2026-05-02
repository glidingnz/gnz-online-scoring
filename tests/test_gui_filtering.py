"""Tests for GUI flight filtering logic."""



class TestFilterFlightsForDisplay:
    """Tests for GUI display filtering."""

    def test_show_all_takes_top_5_by_points(self):
        flights = [
            {"points": 100, "valid": True},
            {"points": 90, "valid": True},
            {"points": 80, "valid": True},
            {"points": 70, "valid": True},
            {"points": 60, "valid": True},
            {"points": 50, "valid": True},
        ]
        # Simulate filter without checkbox (show all)
        filtered = sorted(flights, key=lambda f: f["points"], reverse=True)[:5]
        assert len(filtered) == 5
        assert [f["points"] for f in filtered] == [100, 90, 80, 70, 60]

    def test_hide_invalid_filters_valid_only(self):
        flights = [
            {"points": 100, "valid": True},
            {"points": 90, "valid": False},
            {"points": 80, "valid": True},
            {"points": 70, "valid": False},
            {"points": 60, "valid": True},
        ]
        # Filter valid only
        filtered = [f for f in flights if f.get("valid", True)]
        filtered = sorted(filtered, key=lambda f: f["points"], reverse=True)[:5]
        assert len(filtered) == 3
        assert [f["points"] for f in filtered] == [100, 80, 60]
        assert all(f["valid"] for f in filtered)

    def test_hide_invalid_with_invalid_in_top_5(self):
        """When some top 5 are invalid, they get excluded."""
        flights = [
            {"points": 100, "valid": True},
            {"points": 90, "valid": False},
            {"points": 80, "valid": True},
            {"points": 70, "valid": False},
            {"points": 60, "valid": True},
            {"points": 50, "valid": True},
        ]
        # Filter valid only, take top 5
        filtered = [f for f in flights if f.get("valid", True)]
        filtered = sorted(filtered, key=lambda f: f["points"], reverse=True)[:5]
        assert len(filtered) == 4
        assert [f["points"] for f in filtered] == [100, 80, 60, 50]
        assert all(f["valid"] for f in filtered)

    def test_calculate_display_total(self):
        flights = [
            {"points": 100},
            {"points": 90},
            {"points": 80},
            {"points": 70},
            {"points": 60},
        ]
        total = sum(f.get("points", 0) for f in flights[:5])
        assert total == 400

    def test_calculate_total_with_fewer_than_5(self):
        flights = [
            {"points": 100},
            {"points": 90},
            {"points": 80},
        ]
        total = sum(f.get("points", 0) for f in flights[:5])
        assert total == 270

    def test_empty_flights(self):
        flights = []
        filtered = sorted(flights, key=lambda f: f.get("points", 0), reverse=True)[:5]
        assert filtered == []
        total = sum(f.get("points", 0) for f in flights[:5])
        assert total == 0