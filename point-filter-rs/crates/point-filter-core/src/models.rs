use std::collections::BTreeMap;

/// 系統を表す。
#[derive(Copy, Clone, Debug, Eq, PartialEq, Ord, PartialOrd, Hash)]
pub enum InputSystem {
    Org,
    Grd,
}

impl InputSystem {
    pub fn as_str(self) -> &'static str {
        match self {
            Self::Org => "org",
            Self::Grd => "grd",
        }
    }
}

/// 2 次元座標。
#[derive(Copy, Clone, Debug, PartialEq)]
pub struct Point2D {
    pub x: f64,
    pub y: f64,
}

/// 軸平行矩形。
#[derive(Copy, Clone, Debug, PartialEq)]
pub struct BoundingBox {
    pub min_x: f64,
    pub max_x: f64,
    pub min_y: f64,
    pub max_y: f64,
}

/// 抽出対象の領域。
#[derive(Clone, Debug)]
pub struct Region {
    pub ordinal: u32,
    pub region_id: String,
    pub vertices: Vec<Point2D>,
    pub bounding_box: BoundingBox,
}

/// 入力ファイルの 1 行。
#[derive(Clone, Debug)]
pub struct PointRecord {
    pub raw_line: String,
    pub x: f64,
    pub y: f64,
    pub z: f64,
    pub source_file: std::path::PathBuf,
    pub line_number: usize,
    pub system: InputSystem,
}

/// 処理結果の要約。
#[derive(Clone, Debug, Default)]
pub struct ProcessingReport {
    pub region_count: usize,
    pub input_files: BTreeMap<InputSystem, usize>,
    pub output_counts: BTreeMap<InputSystem, BTreeMap<String, u64>>,
}
