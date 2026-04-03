use std::cmp::Ordering;

use crate::models::{BoundingBox, Point2D};
use crate::validation::{PointFilterError, Result};

/// 数値誤差許容。
pub const EPSILON: f64 = 1e-9;

/// 3 点の外積を返す。
pub fn cross(a: Point2D, b: Point2D, c: Point2D) -> f64 {
    (b.x - a.x) * (c.y - a.y) - (b.y - a.y) * (c.x - a.x)
}

/// 点群を含む最小の軸平行矩形を返す。
pub fn bounding_box_from_points(points: &[Point2D]) -> Result<BoundingBox> {
    let Some(first) = points.first().copied() else {
        return Err(PointFilterError::Geometry(
            "Bounding box requires at least one point".to_string(),
        ));
    };

    let mut min_x = first.x;
    let mut max_x = first.x;
    let mut min_y = first.y;
    let mut max_y = first.y;

    for point in &points[1..] {
        min_x = min_x.min(point.x);
        max_x = max_x.max(point.x);
        min_y = min_y.min(point.y);
        max_y = max_y.max(point.y);
    }

    Ok(BoundingBox {
        min_x,
        max_x,
        min_y,
        max_y,
    })
}

/// 2 つの矩形が交差するかを判定する。
pub fn bounding_boxes_intersect(left: BoundingBox, right: BoundingBox) -> bool {
    !(left.max_x < right.min_x - EPSILON
        || left.min_x > right.max_x + EPSILON
        || left.max_y < right.min_y - EPSILON
        || left.min_y > right.max_y + EPSILON)
}

/// 点が矩形内または境界上にあるかを判定する。
pub fn point_in_bounding_box(point: Point2D, bounding_box: BoundingBox) -> bool {
    (bounding_box.min_x - EPSILON..=bounding_box.max_x + EPSILON).contains(&point.x)
        && (bounding_box.min_y - EPSILON..=bounding_box.max_y + EPSILON).contains(&point.y)
}

/// 凸包を外周順で返す。
pub fn convex_hull(points: &[Point2D]) -> Result<Vec<Point2D>> {
    if points.len() < 3 {
        return Err(PointFilterError::Geometry(
            "Region must have at least 3 points".to_string(),
        ));
    }

    let mut sorted = points.to_vec();
    sorted.sort_by(|left, right| match left.x.total_cmp(&right.x) {
        Ordering::Equal => left.y.total_cmp(&right.y),
        ordering => ordering,
    });

    for pair in sorted.windows(2) {
        if pair[0] == pair[1] {
            return Err(PointFilterError::Geometry(
                "Region contains duplicate points".to_string(),
            ));
        }
    }

    fn build_half(sequence: impl IntoIterator<Item = Point2D>) -> Vec<Point2D> {
        let mut half: Vec<Point2D> = Vec::new();
        for point in sequence {
            while half.len() >= 2
                && cross(half[half.len() - 2], half[half.len() - 1], point) <= EPSILON
            {
                half.pop();
            }
            half.push(point);
        }
        half
    }

    let lower = build_half(sorted.iter().copied());
    let upper = build_half(sorted.iter().rev().copied());
    let mut hull = lower[..lower.len() - 1].to_vec();
    hull.extend_from_slice(&upper[..upper.len() - 1]);

    if hull.len() < 3 {
        return Err(PointFilterError::Geometry(
            "Region has zero area".to_string(),
        ));
    }
    if hull.len() != sorted.len() {
        return Err(PointFilterError::Geometry(
            "Region contains interior or colinear points".to_string(),
        ));
    }

    Ok(hull)
}

/// 点が凸多角形の内部または境界上にあるかを判定する。
pub fn point_in_convex_polygon(point: Point2D, vertices: &[Point2D]) -> bool {
    if vertices.len() < 3 {
        return false;
    }

    let mut sign = 0i8;
    for index in 0..vertices.len() {
        let current = vertices[index];
        let next = vertices[(index + 1) % vertices.len()];
        let value = cross(current, next, point);
        if value.abs() <= EPSILON {
            continue;
        }

        let current_sign = if value > 0.0 { 1 } else { -1 };
        if sign == 0 {
            sign = current_sign;
        } else if sign != current_sign {
            return false;
        }
    }

    true
}
