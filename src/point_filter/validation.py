from __future__ import annotations

from collections.abc import Sequence

from .models import Point2D


class PointFilterError(Exception):
    """Base error for point filter failures."""


class ConfigurationError(PointFilterError):
    """Raised when CLI or configuration is invalid."""


class DataFormatError(PointFilterError):
    """Raised when input data is malformed."""


class GeometryError(PointFilterError):
    """Raised when a polygon is invalid."""


EPSILON = 1e-9


def require_positive_column_index(value: int, label: str) -> None:
    if value < 1:
        raise ConfigurationError(f"{label} column index must be 1 or greater: {value}")


def _cross(a: Point2D, b: Point2D, c: Point2D) -> float:
    return (b.x - a.x) * (c.y - a.y) - (b.y - a.y) * (c.x - a.x)


def _same_sign(a: float, b: float) -> bool:
    return a > 0 and b > 0 or a < 0 and b < 0


def _segments_intersect(a1: Point2D, a2: Point2D, b1: Point2D, b2: Point2D) -> bool:
    def orient(p: Point2D, q: Point2D, r: Point2D) -> float:
        return _cross(p, q, r)

    def on_segment(p: Point2D, q: Point2D, r: Point2D) -> bool:
        return (
            min(p.x, r.x) - EPSILON <= q.x <= max(p.x, r.x) + EPSILON
            and min(p.y, r.y) - EPSILON <= q.y <= max(p.y, r.y) + EPSILON
        )

    o1 = orient(a1, a2, b1)
    o2 = orient(a1, a2, b2)
    o3 = orient(b1, b2, a1)
    o4 = orient(b1, b2, a2)

    if abs(o1) <= EPSILON and on_segment(a1, b1, a2):
        return True
    if abs(o2) <= EPSILON and on_segment(a1, b2, a2):
        return True
    if abs(o3) <= EPSILON and on_segment(b1, a1, b2):
        return True
    if abs(o4) <= EPSILON and on_segment(b1, a2, b2):
        return True

    return not (_same_sign(o1, o2) or _same_sign(o3, o4)) and (
        (o1 > 0 > o2 or o2 > 0 > o1) and (o3 > 0 > o4 or o4 > 0 > o3)
    )


def polygon_area(vertices: Sequence[Point2D]) -> float:
    area2 = 0.0
    for index, current in enumerate(vertices):
        nxt = vertices[(index + 1) % len(vertices)]
        area2 += current.x * nxt.y - nxt.x * current.y
    return abs(area2) / 2.0


def validate_region_vertices(vertices: Sequence[Point2D], region_label: str) -> None:
    if len(vertices) < 3:
        raise GeometryError(f"Region {region_label} must have at least 3 vertices")

    if len({(vertex.x, vertex.y) for vertex in vertices}) != len(vertices):
        raise GeometryError(f"Region {region_label} contains duplicate vertices")

    if polygon_area(vertices) <= EPSILON:
        raise GeometryError(f"Region {region_label} has zero area")

    n = len(vertices)
    non_zero_sign = 0
    for index in range(n):
        a = vertices[index]
        b = vertices[(index + 1) % n]
        c = vertices[(index + 2) % n]
        cross = _cross(a, b, c)
        if abs(cross) <= EPSILON:
            raise GeometryError(f"Region {region_label} has colinear adjacent vertices")
        current_sign = 1 if cross > 0 else -1
        if non_zero_sign == 0:
            non_zero_sign = current_sign
        elif current_sign != non_zero_sign:
            raise GeometryError(f"Region {region_label} is not convex")

    edges = [(vertices[i], vertices[(i + 1) % n]) for i in range(n)]
    for i, (a1, a2) in enumerate(edges):
        for j, (b1, b2) in enumerate(edges):
            if j <= i:
                continue
            if j == i + 1 or (i == 0 and j == n - 1):
                continue
            if _segments_intersect(a1, a2, b1, b2):
                raise GeometryError(f"Region {region_label} self-intersects")
