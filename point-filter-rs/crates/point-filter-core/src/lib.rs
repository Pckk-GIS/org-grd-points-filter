//! 点群抽出の中核ロジック。

pub mod config;
pub mod events;
pub mod filter_service;
pub mod geometry;
pub mod models;
pub mod output_writer;
pub mod point_reader;
pub mod region_loader;
pub mod validation;

pub use config::AppConfig;
pub use events::{ProgressEvent, ProgressSink, SharedProgressSink};
pub use filter_service::process;
pub use models::{BoundingBox, InputSystem, Point2D, ProcessingReport, Region};
pub use validation::{PointFilterError, Result};
