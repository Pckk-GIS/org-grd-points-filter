use std::collections::BTreeMap;
use std::path::Path;

use crate::geometry::{bounding_box_from_points, convex_hull};
use crate::models::{Point2D, Region};
use crate::validation::{PointFilterError, Result, ensure_finite};

const EXPECTED_HEADER: [&str; 3] = ["region_id", "x", "y"];

/// 領域 CSV から複数領域を読み込む。
pub fn load_regions(region_csv: impl AsRef<Path>) -> Result<Vec<Region>> {
    let region_csv = region_csv.as_ref();
    let mut reader = csv::ReaderBuilder::new()
        .has_headers(true)
        .from_path(region_csv)?;

    let header = reader.headers()?.clone();
    let normalized_header: Vec<String> = header
        .iter()
        .map(|column| column.trim().to_lowercase())
        .collect();
    if normalized_header.as_slice() != EXPECTED_HEADER {
        return Err(PointFilterError::InvalidData(format!(
            "Region CSV header must be {:?}, got {:?}",
            EXPECTED_HEADER, normalized_header
        )));
    }

    let mut region_points: BTreeMap<String, Vec<Point2D>> = BTreeMap::new();
    let mut region_order: Vec<String> = Vec::new();

    for (index, result) in reader.records().enumerate() {
        let line_number = index + 2;
        let record = result?;
        if record.iter().all(|field| field.trim().is_empty()) {
            continue;
        }
        if record.len() < 3 {
            return Err(PointFilterError::InvalidData(format!(
                "Region CSV line {} must have at least 3 columns",
                line_number
            )));
        }

        let region_id = record[0].trim().to_string();
        if region_id.is_empty() {
            return Err(PointFilterError::InvalidData(format!(
                "Region CSV line {} must have a non-empty region_id",
                line_number
            )));
        }

        let x = ensure_finite(
            record[1].trim().parse::<f64>().map_err(|_| {
                PointFilterError::InvalidData(format!(
                    "Invalid x value in {} line {}: {:?}",
                    region_csv.display(),
                    line_number,
                    record[1].trim()
                ))
            })?,
            "x",
            region_csv,
            line_number,
        )?;
        let y = ensure_finite(
            record[2].trim().parse::<f64>().map_err(|_| {
                PointFilterError::InvalidData(format!(
                    "Invalid y value in {} line {}: {:?}",
                    region_csv.display(),
                    line_number,
                    record[2].trim()
                ))
            })?,
            "y",
            region_csv,
            line_number,
        )?;

        if !region_points.contains_key(&region_id) {
            region_order.push(region_id.clone());
        }
        region_points
            .entry(region_id)
            .or_default()
            .push(Point2D { x, y });
    }

    if region_order.is_empty() {
        return Err(PointFilterError::InvalidData(format!(
            "Region CSV has no data rows: {}",
            region_csv.display()
        )));
    }

    let mut regions = Vec::with_capacity(region_order.len());
    for (ordinal, region_id) in region_order.into_iter().enumerate() {
        let vertices = convex_hull(
            region_points
                .get(&region_id)
                .expect("region_points must contain all region ids"),
        )?;
        regions.push(Region {
            ordinal: (ordinal + 1) as u32,
            region_id,
            bounding_box: bounding_box_from_points(&vertices)?,
            vertices,
        });
    }

    Ok(regions)
}
