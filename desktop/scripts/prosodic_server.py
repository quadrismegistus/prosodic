"""Standalone server entry point for PyInstaller bundle.

Starts the prosodic FastAPI server on a given port.
Handles ESPEAK_DATA_PATH for bundled espeak.
"""
import os
import sys
import signal


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=0, help='Port to listen on (0 = auto)')
    parser.add_argument('--port-file', type=str, default=None, help='Write chosen port to this file')
    args = parser.parse_args()

    # If running from PyInstaller bundle, set up paths
    if getattr(sys, '_MEIPASS', None):
        bundle_dir = sys._MEIPASS
        # espeak data bundled alongside
        espeak_data = os.path.join(bundle_dir, 'espeak-data')
        if os.path.isdir(espeak_data):
            os.environ['ESPEAK_DATA_PATH'] = espeak_data
        # Bundled espeak binary
        espeak_bin = os.path.join(bundle_dir, 'espeak')
        if os.path.isfile(espeak_bin):
            # Prepend to PATH so subprocess calls find it
            os.environ['PATH'] = os.path.dirname(espeak_bin) + os.pathsep + os.environ.get('PATH', '')

    import uvicorn
    from prosodic.web.api import app

    # Find a free port if 0
    port = args.port
    if port == 0:
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('127.0.0.1', 0))
            port = s.getsockname()[1]

    # Write port to file so Tauri can read it
    if args.port_file:
        with open(args.port_file, 'w') as f:
            f.write(str(port))

    # Clean shutdown on SIGTERM
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))

    print(f"Prosodic server starting on http://127.0.0.1:{port}", flush=True)
    uvicorn.run(app, host='127.0.0.1', port=port, log_level='warning')


if __name__ == '__main__':
    main()
