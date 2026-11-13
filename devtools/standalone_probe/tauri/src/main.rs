//! A thin development window. Scientific state and binary transport stay in Python/Viewer.
use std::{env, fs};
use tauri::WebviewUrl;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let file = env::var("SABUESO_PROBE_BOOTSTRAP")?;
    let bootstrap: serde_json::Value = serde_json::from_slice(&fs::read(file)?)?;
    let url: tauri::Url = bootstrap["url"]
        .as_str()
        .ok_or("Missing bootstrap URL")?
        .parse()?;
    if url.scheme() != "http" || url.host_str() != Some("127.0.0.1") {
        return Err("Expected the owned loopback service".into());
    }
    let mut builder = tauri::Builder::default();
    #[cfg(feature = "webdriver")]
    {
        builder = builder.plugin(tauri_plugin_wdio_webdriver::init());
    }
    builder
        .setup(move |app| {
            tauri::WebviewWindowBuilder::new(app, "probe", WebviewUrl::External(url.clone()))
                .title("Sabueso — standalone integration probe")
                .inner_size(1280.0, 900.0)
                .position(0.0, 0.0)
                .initialization_script_for_all_frames(include_str!("../../browser_observer.js"))
                .on_navigation(|url| {
                    matches!(url.scheme(), "http" | "about")
                        && (url.host_str() == Some("127.0.0.1") || url.scheme() == "about")
                })
                .build()?;
            Ok(())
        })
        .run(tauri::generate_context!())?;
    Ok(())
}
