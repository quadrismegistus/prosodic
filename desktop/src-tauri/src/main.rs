// Prevents additional console window on Windows in release
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::io::{BufRead, BufReader};
use std::process::{Child, Command, Stdio};
use std::sync::Mutex;
use tauri::{Manager, State};

struct ServerState {
    process: Mutex<Option<Child>>,
    port: Mutex<u16>,
}

fn find_sidecar(app_handle: &tauri::AppHandle) -> std::path::PathBuf {
    // In dev mode, look for the PyInstaller output or fall back to python
    let resource_dir = app_handle
        .path()
        .resource_dir()
        .unwrap_or_default();

    // Check for bundled sidecar first
    let sidecar = resource_dir.join("sidecar").join("prosodic-server");
    if sidecar.exists() {
        return sidecar;
    }

    // macOS .app bundle
    let app_sidecar = resource_dir
        .join("prosodic-server")
        .join("prosodic-server");
    if app_sidecar.exists() {
        return app_sidecar;
    }

    // Fallback: use system python (dev mode)
    std::path::PathBuf::from("prosodic-server-not-found")
}

fn start_server(app_handle: &tauri::AppHandle) -> Result<u16, String> {
    let port_file = tempfile::NamedTempFile::new()
        .map_err(|e| format!("Failed to create temp file: {e}"))?;
    let port_path = port_file.path().to_path_buf();

    let sidecar_path = find_sidecar(app_handle);

    let mut child = if sidecar_path.exists() {
        // Use bundled PyInstaller sidecar
        Command::new(&sidecar_path)
            .args(["--port", "0", "--port-file", &port_path.to_string_lossy()])
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .spawn()
            .map_err(|e| format!("Failed to start sidecar: {e}"))?
    } else {
        // Dev mode: run with python directly
        Command::new("python")
            .args([
                "-m", "prosodic.desktop_server",
                "--port", "0",
                "--port-file", &port_path.to_string_lossy(),
            ])
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .spawn()
            .map_err(|e| format!("Failed to start python server: {e}"))?
    };

    // Wait for the server to write its port and print the startup message
    if let Some(stdout) = child.stdout.take() {
        let reader = BufReader::new(stdout);
        for line in reader.lines() {
            if let Ok(line) = line {
                eprintln!("[prosodic-server] {line}");
                if line.contains("starting on") {
                    break;
                }
            }
        }
    }

    // Read port from file
    let port_str = std::fs::read_to_string(&port_path)
        .map_err(|e| format!("Failed to read port file: {e}"))?;
    let port: u16 = port_str
        .trim()
        .parse()
        .map_err(|e| format!("Invalid port: {e}"))?;

    // Store process handle for cleanup
    let state: State<ServerState> = app_handle.state();
    *state.process.lock().unwrap() = Some(child);
    *state.port.lock().unwrap() = port;

    Ok(port)
}

#[tauri::command]
fn get_server_port(state: State<ServerState>) -> u16 {
    *state.port.lock().unwrap()
}

fn main() {
    tauri::Builder::default()
        .manage(ServerState {
            process: Mutex::new(None),
            port: Mutex::new(0),
        })
        .invoke_handler(tauri::generate_handler![get_server_port])
        .setup(|app| {
            let handle = app.handle().clone();

            // Start the Python sidecar
            match start_server(&handle) {
                Ok(port) => {
                    eprintln!("Prosodic server running on port {port}");
                    // Set the port as a JS window property so the frontend can read it
                    if let Some(window) = app.get_webview_window("main") {
                        let _ = window.eval(&format!(
                            "window.__PROSODIC_PORT__ = {port};"
                        ));
                    }
                }
                Err(e) => {
                    eprintln!("Failed to start server: {e}");
                }
            }

            Ok(())
        })
        .on_window_event(|window, event| {
            if let tauri::WindowEvent::Destroyed = event {
                // Kill the sidecar when the window closes
                let state: State<ServerState> = window.state();
                let mut guard = state.process.lock().unwrap();
                if let Some(ref mut child) = *guard {
                    let _ = child.kill();
                    let _ = child.wait();
                }
                *guard = None;
            }
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
