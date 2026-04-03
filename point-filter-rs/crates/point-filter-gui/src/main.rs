mod app;
mod fonts;
mod labels;

use eframe::NativeOptions;

fn main() -> eframe::Result<()> {
    tracing_subscriber::fmt()
        .with_target(false)
        .compact()
        .init();

    let options = NativeOptions::default();
    eframe::run_native(
        labels::APP_TITLE,
        options,
        Box::new(|cc| {
            fonts::configure_japanese_fonts(&cc.egui_ctx);
            Ok(Box::new(app::PointFilterApp::default()))
        }),
    )
}
