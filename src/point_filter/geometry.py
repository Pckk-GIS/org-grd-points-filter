from __future__ import annotations

from collections.abc import Iterable, Sequence

from .models import Point2D
from .validation import GeometryError


EPSILON = 1e-9


def cross(a: Point2D, b: Point2D, c: Point2D) -> float:
    return (b.x - a.x) * (c.y - a.y) - (b.y - a.y) * (c.x - a.x)


def convex_hull(points: Sequence[Point2D]) -> tuple[Point2D, ...]:
    if len(points) < 3:
        raise GeometryError("Region must have at least 3 points")

    if len(set(points)) != len(points):
        raise GeometryError("Region contains duplicate points")

    sorted_points = sorted(points, key=lambda point: (point.x, point.y))

    def build_half(sequence: Iterable[Point2D]) -> list[Point2D]:
        half: list[Point2D] = []
        for point in sequence:
            while len(half) >= 2 and cross(half[-2], half[-1], point) <= EPSILON:
                half.pop()
            half.append(point)
        return half

    lower = build_half(sorted_points)
    upper = build_half(reversed(sorted_points))
    hull = lower[:-1] + upper[:-1]

    if len(hull) < 3:
        raise GeometryError("Region has zero area")
    if len(hull) != len(sorted_points):
        raise GeometryError("Region contains interior or colinear points")

    return tuple(hull)


def point_in_convex_polygon(point: Point2D, vertices: Sequence[Point2D]) -> bool:
    if len(vertices) < 3:
        return False

    sign = 0
    for index, current in enumerate(vertices):
        nxt = vertices[(index + 1) % len(vertices)]
        value = cross(current, nxt, point)
        if abs(value) <= EPSILON:
            continue
        current_sign = 1 if value > 0 else -1
        if sign == 0:
            sign = current_sign
        elif current_sign != sign:
            return False
    return True
