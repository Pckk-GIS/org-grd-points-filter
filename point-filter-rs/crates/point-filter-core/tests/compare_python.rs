use std::fs;
use std::path::{Path, PathBuf};
use std::process::Command;

fn workspace_root() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .expect("crates dir")
        .parent()
        .expect("workspace root")
        .to_path_buf()
}

fn repo_root() -> PathBuf {
    workspace_root().parent().expect("repo root").to_path_buf()
}

fn run_command(mut command: Command, what: &str) {
    let output = command.output().unwrap_or_else(|error| {
        panic!("{what} command could not be executed: {error}");
    });
    if !output.status.success() {
        panic!(
            "{what} failed\nstdout:\n{}\nstderr:\n{}",
            String::from_utf8_lossy(&output.stdout),
            String::from_utf8_lossy(&output.stderr),
        );
    }
}

fn read_bytes(path: &Path) -> Vec<u8> {
    fs::read(path).unwrap_or_else(|error| panic!("failed to read {}: {error}", path.display()))
}

#[test]
fn python_and_rust_outputs_match_on_the_same_input() {
    let root = std::env::temp_dir().join(format!("point-filter-compare-{}", std::process::id()));
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
    let python_output = root.join("python-output");
    let rust_output = root.join("rust-output");
    fs::create_dir_all(&input_dir).expect("input dir");
    fs::create_dir_all(&python_output).expect("python output");
    fs::create_dir_all(&rust_output).expect("rust output");
    fs::write(input_dir.join("sample_org.txt"), "1,5,5,100\n2,25,25,200\n").expect("write org");
    fs::write(input_dir.join("sample_grd.txt"), "1,45,45,300\n").expect("write grd");

    let python_main = repo_root().join("main.py");
    let mut python_command = Command::new("uv");
    python_command.current_dir(repo_root()).args([
        "run",
        "python",
        python_main.to_str().expect("python main path"),
        "--region-csv",
        region_csv.to_str().expect("region path"),
        "--input-dir",
        input_dir.to_str().expect("input path"),
        "--output-dir",
        python_output.to_str().expect("python output path"),
        "--x-col",
        "2",
        "--y-col",
        "3",
        "--z-col",
        "4",
    ]);
    run_command(python_command, "python implementation");

    let mut rust_command = Command::new("cargo");
    rust_command.current_dir(workspace_root()).args([
        "run",
        "--quiet",
        "-p",
        "point-filter-cli",
        "--manifest-path",
        workspace_root()
            .join("Cargo.toml")
            .to_str()
            .expect("workspace manifest"),
        "--",
    ]);
    rust_command.args([
        "--region-csv",
        region_csv.to_str().expect("region path"),
        "--input-dir",
        input_dir.to_str().expect("input path"),
        "--output-dir",
        rust_output.to_str().expect("rust output path"),
        "--x-col",
        "2",
        "--y-col",
        "3",
        "--z-col",
        "4",
    ]);
    run_command(rust_command, "rust implementation");

    for name in [
        "org_region1.txt",
        "org_region2.txt",
        "org_region3.txt",
        "grd_region1.txt",
        "grd_region2.txt",
        "grd_region3.txt",
    ] {
        let python_bytes = read_bytes(&python_output.join(name));
        let rust_bytes = read_bytes(&rust_output.join(name));
        assert_eq!(rust_bytes, python_bytes, "mismatch in {name}");
    }

    let _ = fs::remove_dir_all(&root);
}
