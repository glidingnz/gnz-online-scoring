"""Island polygon definitions and point-in-polygon detection."""

from typing import List, Tuple

Point = Tuple[float, float]

SOUTH_ISLAND_POLYGON: List[Point] = [
    (-40.086, 172.612),
    (-45.748, 165.887),
    (-46.936, 169.670),
    (-41.747, 174.595),
    (-40.524, 174.456),
]

NORTH_ISLAND_POLYGON: List[Point] = [
    (-41.321, 174.570),
    (-41.678, 175.515),
    (-37.516, 178.729),
    (-34.305, 172.598),
    (-39.302, 173.707),
]


def is_point_in_polygon(point: Point, polygon: List[Point]) -> bool:
    """Check if a point is inside a polygon using ray casting.

    Args:
        point: (latitude, longitude) tuple
        polygon: List of (lat, lon) vertices

    Returns:
        True if point is inside polygon
    """
    x, y = point
    n = len(polygon)
    inside = False

    p1x, p1y = polygon[0]
    for i in range(1, n + 1):
        p2x, p2y = polygon[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y

    return inside


def get_island_from_polygon(latitude: float, longitude: float) -> str | None:
    """Determine which island a point belongs to using polygon boundaries.

    Args:
        latitude: latitude coordinate
        longitude: longitude coordinate

    Returns:
        'north', 'south', or None if not in either polygon
    """
    point = (latitude, longitude)

    if is_point_in_polygon(point, NORTH_ISLAND_POLYGON):
        return "north"
    if is_point_in_polygon(point, SOUTH_ISLAND_POLYGON):
        return "south"

    return None