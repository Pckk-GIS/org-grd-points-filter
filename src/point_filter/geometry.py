from __future__ import annotations

from collections.abc import Sequence

from .models import Point2D


EPSILON = 1e-9


def cross(a: Point2D, b: Point2D, c: Point2D) -> float:
    return (b.x - a.x) * (c.y - a.y) - (b.y - a.y) * (c.x - a.x)


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
