use std::path::Path;

use csv::StringRecord;

use crate::models::{InputSystem, PointRecord};
use crate::validation::{PointFilterError, Result, ensure_finite};

/// 入力ファイル名から系統を判定する。
pub fn detect_system_from_filename(path: &Path) -> Option<InputSystem> {
    let stem = path.file_stem()?.to_string_lossy().to_lowercase();
    if stem.ends_with("_org") {
        Some(InputSystem::Org)
    } else if stem.ends_with("_grd") {
        Some(InputSystem::Grd)
    } else {
        None
    }
}

/// 入力フォルダ内の対象テキストを系統ごとにまとめる。
pub fn iter_input_files(
    input_dir: impl AsRef<Path>,
) -> Result<std::collections::BTreeMap<InputSystem, Vec<std::path::PathBuf>>> {
    let input_dir = input_dir.as_ref();
    if !input_dir.exists() {
        return Err(PointFilterError::InvalidData(format!(
            "Input directory not found: {}",
            input_dir.display()
        )));
    }

    let mut grouped: std::collections::BTreeMap<InputSystem, Vec<std::path::PathBuf>> =
        std::collections::BTreeMap::new();
    grouped.insert(InputSystem::Org, Vec::new());
    grouped.insert(InputSystem::Grd, Vec::new());

    let mut entries: Vec<std::path::PathBuf> = std::fs::read_dir(input_dir)?
        .filter_map(|entry| entry.ok().map(|item| item.path()))
        .filter(|path| {
            path.extension()
                .is_some_and(|ext| ext.eq_ignore_ascii_case("txt"))
        })
        .collect();
    entries.sort();

    for path in entries {
        if let Some(system) = detect_system_from_filename(&path) {
            grouped
                .get_mut(&system)
                .expect("system bucket exists")
                .push(path);
        }
    }

    Ok(grouped)
}

/// CSV レコードから 1 行分の点を構築する。
pub fn parse_point_record(
    record: &StringRecord,
    path: &Path,
    line_number: usize,
    x_col: usize,
    y_col: usize,
    z_col: usize,
    system: InputSystem,
) -> Result<PointRecord> {
    let x_index = x_col - 1;
    let y_index = y_col - 1;
    let z_index = z_col - 1;

    let max_index = x_index.max(y_index).max(z_index);
    if max_index >= record.len() {
        return Err(PointFilterError::InvalidData(format!(
            "{} line {} has only {} columns, but columns {}, {}, {} were requested",
            path.display(),
            line_number,
            record.len(),
            x_col,
            y_col,
            z_col
        )));
    }

    let x = ensure_finite(
        record[x_index].trim().parse::<f64>().map_err(|_| {
            PointFilterError::InvalidData(format!(
                "Invalid x value in {} line {}: {:?}",
                path.display(),
                line_number,
                record[x_index].trim()
            ))
        })?,
        "x",
        path,
        line_number,
    )?;
    let y = ensure_finite(
        record[y_index].trim().parse::<f64>().map_err(|_| {
            PointFilterError::InvalidData(format!(
                "Invalid y value in {} line {}: {:?}",
                path.display(),
                line_number,
                record[y_index].trim()
            ))
        })?,
        "y",
        path,
        line_number,
    )?;
    let z = ensure_finite(
        record[z_index].trim().parse::<f64>().map_err(|_| {
            PointFilterError::InvalidData(format!(
                "Invalid z value in {} line {}: {:?}",
                path.display(),
                line_number,
                record[z_index].trim()
            ))
        })?,
        "z",
        path,
        line_number,
    )?;

    Ok(PointRecord {
        raw_line: record.iter().collect::<Vec<_>>().join(","),
        x,
        y,
        z,
        source_file: path.to_path_buf(),
        line_number,
        system,
    })
}
