use std::{fs, path::Path};

use eframe::egui::{self, FontData, FontDefinitions, FontFamily};
use tracing::{info, warn};

const FONT_NAME: &str = "windows-japanese-ui";
const FONT_CANDIDATES: &[&str] = &[
    r"C:\Windows\Fonts\YuGothR.ttc",
    r"C:\Windows\Fonts\YuGothM.ttc",
    r"C:\Windows\Fonts\Meiryo.ttc",
    r"C:\Windows\Fonts\msgothic.ttc",
];

pub fn configure_japanese_fonts(ctx: &egui::Context) {
    let Some((font_path, font_bytes)) = load_font_bytes() else {
        warn!("Japanese UI font was not found. Falling back to egui defaults.");
        return;
    };

    let mut fonts = FontDefinitions::default();
    let mut font_data = FontData::from_owned(font_bytes);
    font_data.index = 0;
    fonts
        .font_data
        .insert(FONT_NAME.to_owned(), font_data.into());

    prepend_font(&mut fonts, FontFamily::Proportional);
    prepend_font(&mut fonts, FontFamily::Monospace);
    ctx.set_fonts(fonts);

    info!("Loaded Japanese UI font: {}", font_path.display());
}

fn load_font_bytes() -> Option<(std::path::PathBuf, Vec<u8>)> {
    FONT_CANDIDATES.iter().find_map(|candidate| {
        let path = Path::new(candidate);
        let bytes = fs::read(path).ok()?;
        Some((path.to_path_buf(), bytes))
    })
}

fn prepend_font(fonts: &mut FontDefinitions, family: FontFamily) {
    if let Some(family_fonts) = fonts.families.get_mut(&family) {
        family_fonts.insert(0, FONT_NAME.to_owned());
    }
}
