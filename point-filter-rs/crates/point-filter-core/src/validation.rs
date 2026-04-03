use std::path::Path;

use thiserror::Error;

/// Rust 版の共通エラー。
#[derive(Debug, Error)]
pub enum PointFilterError {
    #[error("I/O error: {0}")]
    Io(#[from] std::io::Error),
    #[error("CSV error: {0}")]
    Csv(#[from] csv::Error),
    #[error("invalid data: {0}")]
    InvalidData(String),
    #[error("geometry error: {0}")]
    Geometry(String),
    #[error("invalid {field} column index: {index}")]
    InvalidColumnIndex { field: &'static str, index: usize },
    #[error("task join error: {0}")]
    Join(String),
}

/// 共通結果型。
pub type Result<T> = std::result::Result<T, PointFilterError>;

/// 1 始まり列番号が正か検証する。
pub fn require_positive_column_index(index: usize, field: &'static str) -> Result<()> {
    if index == 0 {
        return Err(PointFilterError::InvalidColumnIndex { field, index });
    }
    Ok(())
}

/// 非有限な数値を拒否する。
pub fn ensure_finite(
    value: f64,
    field: &'static str,
    path: &Path,
    line_number: usize,
) -> Result<f64> {
    if value.is_finite() {
        Ok(value)
    } else {
        Err(PointFilterError::InvalidData(format!(
            "Invalid {field} value in {} line {}: {value}",
            path.display(),
            line_number
        )))
    }
}
