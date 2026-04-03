use std::path::PathBuf;
use std::process::ExitCode;

use clap::Parser;
use point_filter_core::{AppConfig, process};
use tracing_subscriber::EnvFilter;

#[derive(Parser, Debug)]
#[command(name = "point-filter")]
#[command(version)]
#[command(about = "Extract points into configured regions.")]
struct Args {
    /// 領域 CSV のパス
    #[arg(long, value_name = "PATH", default_value = "../data/regions.csv")]
    region_csv: PathBuf,
    /// 入力フォルダのパス
    #[arg(long, value_name = "DIR", default_value = "../input")]
    input_dir: PathBuf,
    /// 出力フォルダのパス
    #[arg(long, value_name = "DIR", default_value = "../output-rust")]
    output_dir: PathBuf,
    /// X 座標の列番号。1 始まり。
    #[arg(long, value_name = "N", default_value_t = 2)]
    x_col: usize,
    /// Y 座標の列番号。1 始まり。
    #[arg(long, value_name = "N", default_value_t = 3)]
    y_col: usize,
    /// Z 座標の列番号。1 始まり。
    #[arg(long, value_name = "N", default_value_t = 4)]
    z_col: usize,
    /// org 系統の X 座標列。指定時は --x-col を上書き。
    #[arg(long, value_name = "N")]
    org_x_col: Option<usize>,
    /// org 系統の Y 座標列。指定時は --y-col を上書き。
    #[arg(long, value_name = "N")]
    org_y_col: Option<usize>,
    /// org 系統の Z 座標列。指定時は --z-col を上書き。
    #[arg(long, value_name = "N")]
    org_z_col: Option<usize>,
    /// grd 系統の X 座標列。指定時は --x-col を上書き。
    #[arg(long, value_name = "N")]
    grd_x_col: Option<usize>,
    /// grd 系統の Y 座標列。指定時は --y-col を上書き。
    #[arg(long, value_name = "N")]
    grd_y_col: Option<usize>,
    /// grd 系統の Z 座標列。指定時は --z-col を上書き。
    #[arg(long, value_name = "N")]
    grd_z_col: Option<usize>,
    /// ファイル単位の並列ワーカー数
    #[arg(long, value_name = "N", default_value_t = 2)]
    workers: usize,
    /// `RUST_LOG` に渡すログレベル。例: info, debug
    #[arg(long, value_name = "LEVEL", default_value = "info")]
    log_level: String,
}

fn main() -> ExitCode {
    let args = Args::parse();
    init_logging(&args.log_level);

    match run(args) {
        Ok(()) => ExitCode::SUCCESS,
        Err(error) => {
            eprintln!("error: {error}");
            for cause in error.chain().skip(1) {
                eprintln!("  caused by: {cause}");
            }
            ExitCode::from(1)
        }
    }
}

fn init_logging(log_level: &str) {
    let filter = EnvFilter::try_from_default_env().unwrap_or_else(|_| {
        EnvFilter::try_new(log_level).unwrap_or_else(|_| EnvFilter::new("info"))
    });

    let _ = tracing_subscriber::fmt()
        .with_env_filter(filter)
        .with_target(false)
        .compact()
        .try_init();
}

fn run(args: Args) -> anyhow::Result<()> {
    let mut config = AppConfig::new(
        args.region_csv,
        args.input_dir,
        args.output_dir,
        args.org_x_col.unwrap_or(args.x_col),
        args.org_y_col.unwrap_or(args.y_col),
        args.org_z_col.unwrap_or(args.z_col),
        args.grd_x_col.unwrap_or(args.x_col),
        args.grd_y_col.unwrap_or(args.y_col),
        args.grd_z_col.unwrap_or(args.z_col),
    );
    config.max_workers = args.workers.max(1);

    process(&config, None)?;
    Ok(())
}
