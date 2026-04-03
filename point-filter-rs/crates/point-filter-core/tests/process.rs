use std::fs;
use std::path::PathBuf;
use std::sync::{Arc, Mutex};

use point_filter_core::{
    AppConfig, InputSystem, ProgressEvent, ProgressSink, SharedProgressSink, process,
};

#[derive(Default)]
struct Collector {
    events: Mutex<Vec<ProgressEvent>>,
}

impl ProgressSink for Collector {
    fn emit(&self, event: ProgressEvent) {
        self.events.lock().expect("collector lock").push(event);
    }
}

fn temp_path(name: &str) -> PathBuf {
    std::env::temp_dir().join(format!(
        "point-filter-rs-test-{}-{}",
        name,
        std::process::id()
    ))
}

#[test]
fn process_extracts_points_into_region_id_named_files() {
    let root = temp_path("extracts");
    let _ = fs::remove_dir_all(&root);
    fs::create_dir_all(&root).expect("root dir");

    let region_csv = root.join("regions.csv");
    fs::write(
        &region_csv,
        "region_id,x,y\n\
1,0,0\n\
1,10,0\n\
1,10,10\n\
2,20,20\n\
2,30,20\n\
2,30,30\n\
3,40,40\n\
3,50,40\n\
3,50,50\n",
    )
    .expect("write regions");

    let input_dir = root.join("input");
    let output_dir = root.join("output");
    fs::create_dir_all(&input_dir).expect("input dir");
    fs::create_dir_all(&output_dir).expect("output dir");
    fs::write(input_dir.join("sample_org.txt"), "1,5,5,100\n2,25,25,200\n").expect("write org");
    fs::write(input_dir.join("sample_grd.txt"), "1,45,45,300\n").expect("write grd");

    let collector = Arc::new(Collector::default());
    let sink: SharedProgressSink = collector.clone();

    let report = process(
        &AppConfig {
            region_csv,
            input_dir,
            output_dir: output_dir.clone(),
            org_x_col: 2,
            org_y_col: 3,
            org_z_col: 4,
            grd_x_col: 2,
            grd_y_col: 3,
            grd_z_col: 4,
            max_workers: 2,
        },
        Some(sink),
    )
    .expect("process");

    assert_eq!(report.region_count, 3);
    assert_eq!(report.input_files.get(&InputSystem::Org), Some(&1));
    assert_eq!(report.input_files.get(&InputSystem::Grd), Some(&1));
    assert_eq!(report.output_counts[&InputSystem::Org]["1"], 1);
    assert_eq!(report.output_counts[&InputSystem::Org]["2"], 1);
    assert_eq!(report.output_counts[&InputSystem::Grd]["3"], 1);

    assert_eq!(
        fs::read_to_string(output_dir.join("org_region1.txt")).expect("org r1"),
        "1,5,5,100\n"
    );
    assert_eq!(
        fs::read_to_string(output_dir.join("org_region2.txt")).expect("org r2"),
        "2,25,25,200\n"
    );
    assert_eq!(
        fs::read_to_string(output_dir.join("grd_region3.txt")).expect("grd r3"),
        "1,45,45,300\n"
    );

    let events = collector.events.lock().expect("events");
    assert!(matches!(events[0], ProgressEvent::RegionsLoaded { .. }));
    assert!(matches!(events[1], ProgressEvent::InputScan { .. }));
}
