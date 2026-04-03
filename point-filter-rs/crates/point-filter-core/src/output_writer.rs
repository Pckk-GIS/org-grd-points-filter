use std::collections::BTreeMap;
use std::fs::{self, File};
use std::io::{BufWriter, Write};
use std::path::{Path, PathBuf};

use crate::models::InputSystem;
use crate::validation::Result;

/// 1 出力先の一時ファイルと本番ファイルを表す。
struct OutputFileTarget {
    final_path: PathBuf,
    temp_path: PathBuf,
}

/// 抽出結果を逐次書き込む。
pub struct StreamingOutputWriter {
    targets: BTreeMap<(InputSystem, String), OutputFileTarget>,
    handles: BTreeMap<(InputSystem, String), BufWriter<File>>,
    counts: BTreeMap<InputSystem, BTreeMap<String, u64>>,
    committed: bool,
}

impl StreamingOutputWriter {
    /// 新しいライターを作る。
    pub fn new(output_dir: impl AsRef<Path>, region_ids: &[String]) -> Result<Self> {
        let output_dir = output_dir.as_ref().to_path_buf();
        fs::create_dir_all(&output_dir)?;

        let mut targets = BTreeMap::new();
        let mut handles = BTreeMap::new();
        let mut counts = BTreeMap::new();
        counts.insert(InputSystem::Org, BTreeMap::new());
        counts.insert(InputSystem::Grd, BTreeMap::new());

        for system in [InputSystem::Org, InputSystem::Grd] {
            for region_id in region_ids {
                counts
                    .get_mut(&system)
                    .expect("count bucket exists")
                    .insert(region_id.clone(), 0);
                let final_path =
                    output_dir.join(format!("{}_region{}.txt", system.as_str(), region_id));
                let temp_path =
                    output_dir.join(format!(".{}_region{}.txt.tmp", system.as_str(), region_id));
                let file = File::create(&temp_path)?;
                targets.insert(
                    (system, region_id.clone()),
                    OutputFileTarget {
                        final_path,
                        temp_path,
                    },
                );
                handles.insert((system, region_id.clone()), BufWriter::new(file));
            }
        }

        Ok(Self {
            targets,
            handles,
            counts,
            committed: false,
        })
    }

    /// 1 行書き込む。
    pub fn write(&mut self, system: InputSystem, region_id: &str, line: &str) -> Result<()> {
        let handle = self
            .handles
            .get_mut(&(system, region_id.to_owned()))
            .expect("output handle exists");
        writeln!(handle, "{line}")?;
        *self
            .counts
            .get_mut(&system)
            .expect("count bucket exists")
            .get_mut(region_id)
            .expect("region count exists") += 1;
        Ok(())
    }

    /// 一時ファイルを本番ファイルへ置き換える。
    pub fn commit(&mut self) -> Result<()> {
        if self.committed {
            return Ok(());
        }

        self.close_handles()?;
        for target in self.targets.values() {
            if target.final_path.exists() {
                fs::remove_file(&target.final_path)?;
            }
            fs::rename(&target.temp_path, &target.final_path)?;
        }
        self.committed = true;
        Ok(())
    }

    /// 一時ファイルを破棄する。
    pub fn discard(&mut self) -> Result<()> {
        self.close_handles()?;
        for target in self.targets.values() {
            if target.temp_path.exists() {
                fs::remove_file(&target.temp_path)?;
            }
        }
        Ok(())
    }

    /// 件数のスナップショットを返す。
    pub fn counts(&self) -> BTreeMap<InputSystem, BTreeMap<String, u64>> {
        self.counts.clone()
    }

    fn close_handles(&mut self) -> Result<()> {
        for handle in self.handles.values_mut() {
            handle.flush()?;
        }
        self.handles.clear();
        Ok(())
    }
}
