use std::path::PathBuf;
use std::sync::Arc;

use crate::models::InputSystem;

/// 進捗を通知するイベント。
#[derive(Clone, Debug)]
pub enum ProgressEvent {
    RegionsLoaded {
        region_count: usize,
        region_ids: Vec<String>,
    },
    InputScan {
        org_files: usize,
        grd_files: usize,
        total_files: usize,
    },
    FileStart {
        system: InputSystem,
        path: PathBuf,
        index: usize,
        total: usize,
    },
    FileProgress {
        system: InputSystem,
        path: PathBuf,
        index: usize,
        total: usize,
        records: usize,
    },
    FileDone {
        system: InputSystem,
        path: PathBuf,
        index: usize,
        total: usize,
        records: usize,
        matches: std::collections::BTreeMap<String, u64>,
    },
    OutputStart,
    OutputFile {
        path: PathBuf,
        count: u64,
    },
    OutputDone,
}

/// 進捗イベントの送出先。
pub trait ProgressSink: Send + Sync {
    fn emit(&self, event: ProgressEvent);
}

impl<F> ProgressSink for F
where
    F: Fn(ProgressEvent) + Send + Sync,
{
    fn emit(&self, event: ProgressEvent) {
        self(event);
    }
}

/// 共有しやすい進捗送出先。
pub type SharedProgressSink = Arc<dyn ProgressSink>;
