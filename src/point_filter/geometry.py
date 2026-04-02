"""幾何演算の補助関数をまとめる。"""

from __future__ import annotations

from collections.abc import Iterable, Sequence

from .models import BoundingBox, Point2D
from .validation import GeometryError


EPSILON = 1e-9


def cross(a: Point2D, b: Point2D, c: Point2D) -> float:
    """3 点の外積を返す。"""
    return (b.x - a.x) * (c.y - a.y) - (b.y - a.y) * (c.x - a.x)


def bounding_box_from_points(points: Sequence[Point2D]) -> BoundingBox:
    """点群を含む軸平行な最小矩形を返す。"""
    if not points:
        raise GeometryError("Bounding box requires at least one point")

    xs = [point.x for point in points]
    ys = [point.y for point in points]
    return BoundingBox(min(xs), max(xs), min(ys), max(ys))


def bounding_boxes_intersect(left: BoundingBox, right: BoundingBox) -> bool:
    """2 つの矩形が交差するかを判定する。"""
    return not (
        left.max_x < right.min_x - EPSILON
        or left.min_x > right.max_x + EPSILON
        or left.max_y < right.min_y - EPSILON
        or left.min_y > right.max_y + EPSILON
    )


def point_in_bounding_box(point: Point2D, bounding_box: BoundingBox) -> bool:
    """点が矩形内または境界上にあるか判定する。"""
    return (
        bounding_box.min_x - EPSILON <= point.x <= bounding_box.max_x + EPSILON
        and bounding_box.min_y - EPSILON <= point.y <= bounding_box.max_y + EPSILON
    )


def convex_hull(points: Sequence[Point2D]) -> tuple[Point2D, ...]:
    """凸多角形の頂点列を外周順に返す。"""
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
    """点が凸多角形の内部または境界上にあるか判定する。"""
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
