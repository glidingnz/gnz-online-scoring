"""Flight selection utilities."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


def select_top_flights(flights: list, max_count: int = 5) -> list:
    """Select top flights.
    
    Algorithm:
    1. Sort all flights by points (descending)
    2. Walk through from highest to lowest
    3. Include flights until you've included the 5th valid flight
    4. Once 5th valid is included, STOP - don't include any more
    """
    if not flights:
        return []
    
    # Sort by points descending
    sorted_flights = sorted(flights, key=lambda f: f.points, reverse=True)
    
    result = []
    valid_count = 0
    
    for flight in sorted_flights:
        result.append(flight)
        
        if flight.valid:
            valid_count += 1
            # Stop AFTER including the max_count-th valid
            if valid_count >= max_count:
                break
    
    return result