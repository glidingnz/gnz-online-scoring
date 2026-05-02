"""Tests for flight selection logic."""



class MockFlight:
    def __init__(self, id: int, points: float, valid: bool):
        self.id = id
        self.points = points
        self.valid = valid


def test_all_valid_takes_top_5():
    from app.selection import select_top_flights
    flights = [
        MockFlight(1, 100, True),
        MockFlight(2, 90, True),
        MockFlight(3, 80, True),
        MockFlight(4, 70, True),
        MockFlight(5, 60, True),
        MockFlight(6, 50, True),
    ]
    result = select_top_flights(flights, 5)
    # All valid - exactly 5
    assert len(result) == 5
    assert [f.id for f in result] == [1, 2, 3, 4, 5]


def test_5th_invalid_includes_6th_valid():
    from app.selection import select_top_flights
    # 5th is invalid, 6th is valid - include both to get 5th valid
    flights = [
        MockFlight(1, 100, True),
        MockFlight(2, 90, True),
        MockFlight(3, 80, True),
        MockFlight(4, 70, True),
        MockFlight(5, 60, False),  # position 5 - invalid
        MockFlight(6, 50, True),   # position 6 - valid (fills out the 5th valid slot)
    ]
    result = select_top_flights(flights, 5)
    # Include positions 1-6 to get 5 valid flights
    assert len(result) == 6
    assert [f.id for f in result] == [1, 2, 3, 4, 5, 6]
    # Last one should be valid (the 5th valid)
    assert result[-1].valid is True


def test_all_invalid_takes_all():
    from app.selection import select_top_flights
    flights = [
        MockFlight(1, 100, False),
        MockFlight(2, 90, False),
        MockFlight(3, 80, False),
    ]
    result = select_top_flights(flights, 5)
    # No valid flights exist, include all
    assert len(result) == 3
    assert [f.id for f in result] == [1, 2, 3]


def test_many_invalid_before_5th_valid():
    from app.selection import select_top_flights
    # 3 invalid in top 6, valid at positions 1,4,6,7,8 (5 valid by position 8)
    flights = [
        MockFlight(1, 100, True),
        MockFlight(2, 90, False),
        MockFlight(3, 80, False),
        MockFlight(4, 70, True),
        MockFlight(5, 60, False),
        MockFlight(6, 50, True),
        MockFlight(7, 40, True),
        MockFlight(8, 30, True),
    ]
    result = select_top_flights(flights, 5)
    # Need positions 1-8 to get 5 valid
    assert len(result) == 8
    valid_count = sum(1 for f in result if f.valid)
    assert valid_count == 5