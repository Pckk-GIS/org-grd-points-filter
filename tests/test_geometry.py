from point_filter.geometry import point_in_convex_polygon
from point_filter.models import Point2D


def test_point_in_convex_polygon_includes_boundary():
    vertices = (
        Point2D(0.0, 0.0),
        Point2D(10.0, 0.0),
        Point2D(10.0, 10.0),
        Point2D(0.0, 10.0),
    )

    assert point_in_convex_polygon(Point2D(5.0, 5.0), vertices)
    assert point_in_convex_polygon(Point2D(0.0, 5.0), vertices)
    assert not point_in_convex_polygon(Point2D(11.0, 5.0), vertices)
