use std::path::PathBuf;

/// Rust 版の実行設定。
#[derive(Clone, Debug)]
pub struct AppConfig {
    pub region_csv: PathBuf,
    pub input_dir: PathBuf,
    pub output_dir: PathBuf,
    pub org_x_col: usize,
    pub org_y_col: usize,
    pub org_z_col: usize,
    pub grd_x_col: usize,
    pub grd_y_col: usize,
    pub grd_z_col: usize,
    pub max_workers: usize,
}

impl AppConfig {
    #[allow(clippy::too_many_arguments)]
    pub fn new(
        region_csv: PathBuf,
        input_dir: PathBuf,
        output_dir: PathBuf,
        org_x_col: usize,
        org_y_col: usize,
        org_z_col: usize,
        grd_x_col: usize,
        grd_y_col: usize,
        grd_z_col: usize,
    ) -> Self {
        Self {
            region_csv,
            input_dir,
            output_dir,
            org_x_col,
            org_y_col,
            org_z_col,
            grd_x_col,
            grd_y_col,
            grd_z_col,
            max_workers: 2,
        }
    }

    pub fn with_shared_columns(
        region_csv: PathBuf,
        input_dir: PathBuf,
        output_dir: PathBuf,
        x_col: usize,
        y_col: usize,
        z_col: usize,
    ) -> Self {
        Self::new(
            region_csv, input_dir, output_dir, x_col, y_col, z_col, x_col, y_col, z_col,
        )
    }

    pub fn columns_for(&self, system: crate::models::InputSystem) -> (usize, usize, usize) {
        match system {
            crate::models::InputSystem::Org => (self.org_x_col, self.org_y_col, self.org_z_col),
            crate::models::InputSystem::Grd => (self.grd_x_col, self.grd_y_col, self.grd_z_col),
        }
    }
}
