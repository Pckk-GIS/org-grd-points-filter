use std::collections::BTreeMap;
use std::fs;
use std::io::{BufRead, BufReader};
use std::path::PathBuf;
use std::sync::Arc;

use rayon::prelude::*;

use crate::config::AppConfig;
use crate::events::{ProgressEvent, SharedProgressSink};
use crate::geometry::{point_in_bounding_box, point_in_convex_polygon};
use crate::models::{InputSystem, Point2D, ProcessingReport, Region};
use crate::output_writer::StreamingOutputWriter;
use crate::point_reader::{iter_input_files, parse_point_record};
use crate::region_loader::load_regions;
use crate::validation::{PointFilterError, Result, require_positive_column_index};

#[derive(Clone, Debug)]
struct FileTask {
    system: InputSystem,
    index: usize,
    total: usize,
    path: PathBuf,
}

#[derive(Clone, Debug)]
struct FileTaskResult {
    system: InputSystem,
    index: usize,
    total: usize,
    path: PathBuf,
    temp_dir: PathBuf,
    records: usize,
    matches: BTreeMap<String, u64>,
}

/// 設定に従って点群を定義済み領域へ振り分ける。
pub fn process(
    config: &AppConfig,
    progress_sink: Option<SharedProgressSink>,
) -> Result<ProcessingReport> {
    require_positive_column_index(config.org_x_col, "org X")?;
    require_positive_column_index(config.org_y_col, "org Y")?;
    require_positive_column_index(config.org_z_col, "org Z")?;
    require_positive_column_index(config.grd_x_col, "grd X")?;
    require_positive_column_index(config.grd_y_col, "grd Y")?;
    require_positive_column_index(config.grd_z_col, "grd Z")?;

    let regions = Arc::new(load_regions(&config.region_csv)?);
    let region_ids: Vec<String> = regions
        .iter()
        .map(|region| region.region_id.clone())
        .collect();
    emit(
        progress_sink.as_ref(),
        ProgressEvent::RegionsLoaded {
            region_count: regions.len(),
            region_ids: region_ids.clone(),
        },
    );

    let grouped_input_files = iter_input_files(&config.input_dir)?;
    let org_total = grouped_input_files
        .get(&InputSystem::Org)
        .map(|paths| paths.len())
        .unwrap_or_default();
    let grd_total = grouped_input_files
        .get(&InputSystem::Grd)
        .map(|paths| paths.len())
        .unwrap_or_default();
    emit(
        progress_sink.as_ref(),
        ProgressEvent::InputScan {
            org_files: org_total,
            grd_files: grd_total,
            total_files: org_total + grd_total,
        },
    );

    let input_file_counts =
        BTreeMap::from([(InputSystem::Org, org_total), (InputSystem::Grd, grd_total)]);
    let tasks = build_file_tasks(&grouped_input_files);

    if tasks.is_empty() {
        let mut writer = StreamingOutputWriter::new(&config.output_dir, &region_ids)?;
        writer.commit()?;
        return Ok(ProcessingReport {
            region_count: regions.len(),
            input_files: input_file_counts,
            output_counts: writer.counts(),
        });
    }

    for task in &tasks {
        emit(
            progress_sink.as_ref(),
            ProgressEvent::FileStart {
                system: task.system,
                path: task.path.clone(),
                index: task.index,
                total: task.total,
            },
        );
    }

    let sink = progress_sink.clone();
    let pool = rayon::ThreadPoolBuilder::new()
        .num_threads(config.max_workers.max(1))
        .build()
        .map_err(|error| PointFilterError::Join(error.to_string()))?;

    let results: Result<Vec<FileTaskResult>> = pool.install(|| {
        tasks
            .into_par_iter()
            .map(|task| process_file_task(task, Arc::clone(&regions), config, sink.clone()))
            .collect()
    });
    let results = results?;

    let mut final_writer = StreamingOutputWriter::new(&config.output_dir, &region_ids)?;
    for result in results {
        merge_partial_result(&mut final_writer, &result, regions.as_ref())?;
        emit(
            progress_sink.as_ref(),
            ProgressEvent::FileDone {
                system: result.system,
                path: result.path,
                index: result.index,
                total: result.total,
                records: result.records,
                matches: result.matches,
            },
        );
        fs::remove_dir_all(&result.temp_dir)?;
    }

    emit(progress_sink.as_ref(), ProgressEvent::OutputStart);
    final_writer.commit()?;
    let output_counts = final_writer.counts();
    for (system, region_counts) in &output_counts {
        for (region_id, count) in region_counts {
            emit(
                progress_sink.as_ref(),
                ProgressEvent::OutputFile {
                    path: config.output_dir.join(format!(
                        "{}_region{}.txt",
                        system.as_str(),
                        region_id
                    )),
                    count: *count,
                },
            );
        }
    }
    emit(progress_sink.as_ref(), ProgressEvent::OutputDone);

    Ok(ProcessingReport {
        region_count: regions.len(),
        input_files: input_file_counts,
        output_counts,
    })
}

fn emit(progress_sink: Option<&SharedProgressSink>, event: ProgressEvent) {
    if let Some(sink) = progress_sink {
        sink.emit(event);
    }
}

fn build_file_tasks(grouped_input_files: &BTreeMap<InputSystem, Vec<PathBuf>>) -> Vec<FileTask> {
    let mut tasks = Vec::new();
    for system in [InputSystem::Org, InputSystem::Grd] {
        let Some(paths) = grouped_input_files.get(&system) else {
            continue;
        };
        let total = paths.len();
        for (index, path) in paths.iter().enumerate() {
            tasks.push(FileTask {
                system,
                index: index + 1,
                total,
                path: path.clone(),
            });
        }
    }
    tasks
}

fn process_file_task(
    task: FileTask,
    regions: Arc<Vec<Region>>,
    config: &AppConfig,
    progress_sink: Option<SharedProgressSink>,
) -> Result<FileTaskResult> {
    let temp_dir = tempfile::Builder::new()
        .prefix(&format!(
            "point-filter-rs-{}-{}",
            task.system.as_str(),
            task.index
        ))
        .tempdir()?
        .keep();
    let region_ids: Vec<String> = regions
        .iter()
        .map(|region| region.region_id.clone())
        .collect();
    let mut writer = StreamingOutputWriter::new(&temp_dir, &region_ids)?;
    let mut matches: BTreeMap<String, u64> = BTreeMap::new();
    for region in regions.iter() {
        matches.insert(region.region_id.clone(), 0);
    }

    let file = fs::File::open(&task.path)?;
    let mut reader = csv::ReaderBuilder::new()
        .has_headers(false)
        .from_reader(BufReader::new(file));

    let mut record = csv::StringRecord::new();
    let mut processed = 0usize;
    while reader.read_record(&mut record)? {
        let line_number = reader.position().line() as usize;
        if record.iter().all(|field| field.trim().is_empty()) {
            record.clear();
            continue;
        }

        let (x_col, y_col, z_col) = config.columns_for(task.system);
        let point_record = parse_point_record(
            &record,
            &task.path,
            line_number,
            x_col,
            y_col,
            z_col,
            task.system,
        )?;

        processed += 1;
        let point = Point2D {
            x: point_record.x,
            y: point_record.y,
        };
        for region in regions.iter() {
            if !point_in_bounding_box(point, region.bounding_box) {
                continue;
            }
            if point_in_convex_polygon(point, &region.vertices) {
                writer.write(task.system, &region.region_id, &point_record.raw_line)?;
                *matches
                    .get_mut(&region.region_id)
                    .expect("region count exists") += 1;
            }
        }

        if processed.is_multiple_of(100_000) {
            emit(
                progress_sink.as_ref(),
                ProgressEvent::FileProgress {
                    system: task.system,
                    path: task.path.clone(),
                    index: task.index,
                    total: task.total,
                    records: processed,
                },
            );
        }

        record.clear();
    }

    writer.commit()?;

    Ok(FileTaskResult {
        system: task.system,
        index: task.index,
        total: task.total,
        path: task.path,
        temp_dir,
        records: processed,
        matches,
    })
}

fn merge_partial_result(
    writer: &mut StreamingOutputWriter,
    result: &FileTaskResult,
    regions: &[Region],
) -> Result<()> {
    for region in regions {
        let part_path = result.temp_dir.join(format!(
            "{}_region{}.txt",
            result.system.as_str(),
            region.region_id
        ));
        if !part_path.exists() {
            continue;
        }

        let file = fs::File::open(&part_path)?;
        for line in BufReader::new(file).lines() {
            writer.write(result.system, &region.region_id, &line?)?;
        }
    }
    Ok(())
}
