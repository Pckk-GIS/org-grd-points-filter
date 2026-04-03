use std::path::PathBuf;
use std::sync::mpsc::{self, Receiver, Sender};
use std::thread;

use eframe::egui;
use point_filter_core::{
    AppConfig, ProcessingReport, ProgressEvent, ProgressSink, SharedProgressSink, process,
};

use crate::labels;

const HELP_TEXT: &str = r#"このツールは、入力フォルダ内の org / grd 点群テキストを、領域 CSV に基づいて複数領域へ振り分けます。

使い方:
1. 領域 CSV を選ぶ
2. 入力フォルダを選ぶ
3. 出力フォルダを選ぶ
4. X / Y / Z の列番号を 1 始まりで指定する
5. 実行する

CSV 仕様:
- region_id,x,y の 3 列
- 1 行 = 1 頂点
- 同じ region_id の点群から自動で凸包を作成

入力仕様:
- 列名なし
- 列番号は 1 始まり
- ヘッダ行なしを前提

出力:
- org_region{region_id}.txt
- grd_region{region_id}.txt

補足:
- 境界上の点は含めます
- 出力は逐次書き込みです
- 処理はファイル単位で並列化されます
"#;

enum GuiMessage {
    Progress(ProgressEvent),
    Finished(Result<ProcessingReport, String>),
}

struct ChannelSink {
    sender: Sender<GuiMessage>,
}

impl ProgressSink for ChannelSink {
    fn emit(&self, event: ProgressEvent) {
        let _ = self.sender.send(GuiMessage::Progress(event));
    }
}

pub struct PointFilterApp {
    region_csv: String,
    input_dir: String,
    output_dir: String,
    x_col: String,
    y_col: String,
    z_col: String,
    workers: String,
    running: bool,
    status: String,
    logs: Vec<String>,
    receiver: Option<Receiver<GuiMessage>>,
    help_open: bool,
}

impl Default for PointFilterApp {
    fn default() -> Self {
        Self {
            region_csv: "../data/regions.csv".to_string(),
            input_dir: "../input".to_string(),
            output_dir: "../output-rust".to_string(),
            x_col: "2".to_string(),
            y_col: "3".to_string(),
            z_col: "4".to_string(),
            workers: "2".to_string(),
            running: false,
            status: labels::STATUS_IDLE.to_string(),
            logs: Vec::new(),
            receiver: None,
            help_open: false,
        }
    }
}

impl PointFilterApp {
    fn append_log(&mut self, message: impl Into<String>) {
        self.logs.push(message.into());
    }

    fn push_progress_log(&mut self, event: ProgressEvent) {
        match event {
            ProgressEvent::RegionsLoaded { region_count, .. } => {
                self.append_log(format!("領域CSVを読み込みました: {region_count} 領域"));
            }
            ProgressEvent::InputScan {
                org_files,
                grd_files,
                total_files,
            } => {
                self.append_log(format!(
                    "入力ファイルを確認しました: org={org_files} 件, grd={grd_files} 件, 合計={total_files} 件"
                ));
            }
            ProgressEvent::FileStart {
                system,
                path,
                index,
                total,
            } => {
                self.append_log(format!(
                    "[{}] 読み込み開始: {} ({}/{})",
                    system.as_str(),
                    path.display(),
                    index,
                    total
                ));
            }
            ProgressEvent::FileProgress {
                system,
                path,
                records,
                ..
            } => {
                self.append_log(format!(
                    "[{}] 読み込み中: {} ({} 行処理済み)",
                    system.as_str(),
                    path.display(),
                    records
                ));
            }
            ProgressEvent::FileDone {
                system,
                path,
                index,
                total,
                records,
                matches,
            } => {
                let summary = matches
                    .iter()
                    .map(|(region_id, count)| format!("region{region_id}={count}"))
                    .collect::<Vec<_>>()
                    .join(", ");
                self.append_log(format!(
                    "[{}] 読み込み完了: {} ({}/{}, {} 行, {})",
                    system.as_str(),
                    path.display(),
                    index,
                    total,
                    records,
                    summary
                ));
            }
            ProgressEvent::OutputStart => self.append_log("出力ファイルを書き出します。"),
            ProgressEvent::OutputFile { path, count } => {
                self.append_log(format!("出力: {} ({} 行)", path.display(), count));
            }
            ProgressEvent::OutputDone => self.append_log("出力ファイルの書き出しが完了しました。"),
        }
    }

    fn parse_config(&self) -> Result<AppConfig, String> {
        let region_csv = PathBuf::from(self.region_csv.trim());
        let input_dir = PathBuf::from(self.input_dir.trim());
        let output_dir = PathBuf::from(self.output_dir.trim());
        let x_col = self
            .x_col
            .trim()
            .parse::<usize>()
            .map_err(|error| format!("X列の指定が不正です: {} ({error})", self.x_col.trim()))?;
        let y_col = self
            .y_col
            .trim()
            .parse::<usize>()
            .map_err(|error| format!("Y列の指定が不正です: {} ({error})", self.y_col.trim()))?;
        let z_col = self
            .z_col
            .trim()
            .parse::<usize>()
            .map_err(|error| format!("Z列の指定が不正です: {} ({error})", self.z_col.trim()))?;
        let workers = self.workers.trim().parse::<usize>().map_err(|error| {
            format!(
                "ワーカー数の指定が不正です: {} ({error})",
                self.workers.trim()
            )
        })?;

        if workers == 0 {
            return Err("ワーカー数は 1 以上で指定してください。".to_string());
        }

        let mut config =
            AppConfig::with_shared_columns(region_csv, input_dir, output_dir, x_col, y_col, z_col);
        config.max_workers = workers;
        Ok(config)
    }

    fn start_process(&mut self) {
        if self.running {
            return;
        }

        let config = match self.parse_config() {
            Ok(config) => config,
            Err(message) => {
                self.status = "設定エラー".to_string();
                self.append_log(format!("設定エラー: {message}"));
                return;
            }
        };

        let (sender, receiver) = mpsc::channel::<GuiMessage>();
        self.receiver = Some(receiver);
        self.running = true;
        self.status = labels::STATUS_RUNNING.to_string();
        self.append_log("処理を開始します。");
        self.append_log("設定を確認しました。");
        self.append_log(format!(
            "設定: 領域CSV={}, 入力フォルダ={}, 出力フォルダ={}, X={}, Y={}, Z={}, workers={}",
            config.region_csv.display(),
            config.input_dir.display(),
            config.output_dir.display(),
            config.org_x_col,
            config.org_y_col,
            config.org_z_col,
            config.max_workers
        ));

        thread::spawn(move || {
            let sink: SharedProgressSink = std::sync::Arc::new(ChannelSink {
                sender: sender.clone(),
            });
            let result = process(&config, Some(sink)).map_err(|error| error.to_string());
            let _ = sender.send(GuiMessage::Finished(result));
        });
    }

    fn poll_messages(&mut self) {
        let mut events = Vec::new();
        let mut finished: Option<Result<ProcessingReport, String>> = None;
        let mut disconnected = false;

        if let Some(receiver) = self.receiver.as_ref() {
            loop {
                match receiver.try_recv() {
                    Ok(GuiMessage::Progress(event)) => events.push(event),
                    Ok(GuiMessage::Finished(result)) => {
                        finished = Some(result);
                        break;
                    }
                    Err(std::sync::mpsc::TryRecvError::Empty) => break,
                    Err(std::sync::mpsc::TryRecvError::Disconnected) => {
                        disconnected = true;
                        break;
                    }
                }
            }
        }

        for event in events {
            self.push_progress_log(event);
        }

        if let Some(result) = finished {
            self.running = false;
            match result {
                Ok(report) => {
                    self.status = format!(
                        "完了: 領域数={}, 出力件数={:?}",
                        report.region_count, report.output_counts
                    );
                    self.append_log("処理が完了しました。");
                }
                Err(error) => {
                    self.status = "失敗".to_string();
                    self.append_log(format!("エラー: {error}"));
                }
            }
            self.receiver = None;
        } else if disconnected {
            self.running = false;
            self.status = "失敗".to_string();
            self.append_log("エラー: ワーカースレッドとの接続が切れました。");
            self.receiver = None;
        }
    }

    fn draw_menu(&mut self, ui: &mut egui::Ui) {
        ui.menu_button(labels::MENU_HELP, |ui| {
            if ui.button(labels::MENU_HELP_USAGE).clicked() {
                self.help_open = true;
                ui.close();
            }
            if ui.button(labels::MENU_HELP_EXIT).clicked() {
                ui.ctx().send_viewport_cmd(egui::ViewportCommand::Close);
            }
        });
    }

    fn draw_help_window(&mut self, ctx: &egui::Context) {
        if self.help_open {
            egui::Window::new(labels::HELP_TITLE)
                .open(&mut self.help_open)
                .resizable(true)
                .vscroll(true)
                .show(ctx, |ui| {
                    ui.label(HELP_TEXT);
                });
        }
    }
}

impl eframe::App for PointFilterApp {
    fn update(&mut self, ctx: &egui::Context, _frame: &mut eframe::Frame) {
        self.poll_messages();

        egui::TopBottomPanel::top("menu").show(ctx, |ui| {
            egui::MenuBar::new().ui(ui, |ui| {
                self.draw_menu(ui);
            });
        });

        egui::CentralPanel::default().show(ctx, |ui| {
            ui.horizontal(|ui| {
                ui.heading(labels::APP_TITLE);
                ui.label(&self.status);
            });
            ui.label(labels::RUN_HINT);
            ui.separator();

            egui::Grid::new("form_grid")
                .num_columns(3)
                .spacing([12.0, 8.0])
                .show(ui, |ui| {
                    ui.label(labels::LABEL_REGION_CSV);
                    ui.text_edit_singleline(&mut self.region_csv);
                    if ui.button(labels::BUTTON_BROWSE).clicked()
                        && let Some(path) = rfd::FileDialog::new()
                            .add_filter("CSV", &["csv"])
                            .pick_file()
                    {
                        self.region_csv = path.display().to_string();
                    }
                    ui.end_row();

                    ui.label(labels::LABEL_INPUT_DIR);
                    ui.text_edit_singleline(&mut self.input_dir);
                    if ui.button(labels::BUTTON_BROWSE).clicked()
                        && let Some(path) = rfd::FileDialog::new().pick_folder()
                    {
                        self.input_dir = path.display().to_string();
                    }
                    ui.end_row();

                    ui.label(labels::LABEL_OUTPUT_DIR);
                    ui.text_edit_singleline(&mut self.output_dir);
                    if ui.button(labels::BUTTON_BROWSE).clicked()
                        && let Some(path) = rfd::FileDialog::new().pick_folder()
                    {
                        self.output_dir = path.display().to_string();
                    }
                    ui.end_row();

                    ui.label(labels::LABEL_X_COL);
                    ui.text_edit_singleline(&mut self.x_col);
                    ui.label(labels::LABEL_Y_COL);
                    ui.end_row();

                    ui.label(labels::LABEL_Z_COL);
                    ui.text_edit_singleline(&mut self.z_col);
                    ui.label(labels::LABEL_WORKERS);
                    ui.end_row();

                    ui.label("");
                    ui.text_edit_singleline(&mut self.workers);
                    ui.label("");
                    ui.end_row();
                });

            ui.horizontal(|ui| {
                if ui
                    .add_enabled(!self.running, egui::Button::new(labels::BUTTON_RUN))
                    .clicked()
                {
                    self.start_process();
                }
                if ui.button(labels::BUTTON_CLEAR_LOG).clicked() {
                    self.logs.clear();
                }
            });

            ui.separator();
            egui::ScrollArea::vertical()
                .stick_to_bottom(true)
                .show(ui, |ui| {
                    for line in &self.logs {
                        ui.label(line);
                    }
                });
        });

        self.draw_help_window(ctx);

        if self.running {
            ctx.request_repaint_after(std::time::Duration::from_millis(100));
        }
    }
}
