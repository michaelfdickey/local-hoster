# Local Hoster

A lightweight desktop app to track, launch, and restart locally hosted web applications.

## Features

- **Track** all your local web apps in one place (name, frontend URL, backend URL)
- **Start / Stop / Restart** apps with one click via their `launcher.py` (Windows) or `launcher.sh` (macOS/Linux)
- **Auto-detect** launcher scripts in each project folder
- **Persist** configuration across launches via `config.json`
- **Add / Edit / Remove** apps through a built-in dialog with a folder browser
- **GitHub repo** link stored alongside each project
- Cross-platform: Windows and macOS

## Tech Stack

| Layer    | Technology          |
|----------|---------------------|
| Frontend | QML (Qt Quick)      |
| Backend  | Python + PySide6    |
| Config   | JSON (`config.json`)|

## Project Structure

```
local-hoster/
├── launcher.py          # Creates venv, installs deps, launches the app
├── requirements.txt     # PySide6
├── config.json          # Persisted app list (auto-managed)
├── README.md
└── src/
    ├── main.py          # Application entry point
    ├── app_manager.py   # Backend model & process management
    └── qml/
        ├── Main.qml         # Main window with app list
        └── AddAppDialog.qml # Add / Edit dialog
```

## Getting Started

### Quick Start (recommended)

```bash
python launcher.py
```

This will:
1. Create a virtual environment in `./venv`
2. Install PySide6 from `requirements.txt`
3. Launch the application

### Manual Setup

```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
python src/main.py
```

## How It Works

Each tracked web app must have a **launcher script** in its project folder:

| OS              | Expected Script |
|-----------------|-----------------|
| Windows         | `launcher.py`   |
| macOS / Linux   | `launcher.sh`   |

The launcher script is responsible for activating the project's own virtual environment (if any) and starting the web server. Local Hoster starts / stops these scripts as child processes.

### Launcher `--stop` Convention

Local Hoster invokes the launcher with `--stop` when the user clicks Stop or Restart. The launcher **must** handle this switch to cleanly kill the running server. The recommended pattern is to use a PID file.

### Windows `launcher.py` Template

Below is a complete working template for a Windows `launcher.py`. Copy this into any tracked app's project folder and adapt the `MAIN_SCRIPT` path and server start command to match your project:

```python
#!/usr/bin/env python3
"""
launcher.py - Windows launcher for use with Local Hoster.

Supports:
    python launcher.py          # Start the app
    python launcher.py --stop   # Stop the app via PID file
"""

import os
import sys
import subprocess
import platform

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
VENV_DIR = os.path.join(ROOT_DIR, "venv")
PID_FILE = os.path.join(ROOT_DIR, ".server.pid")

# --- EDIT THIS: path to your server entry point ---
MAIN_SCRIPT = os.path.join(ROOT_DIR, "src", "main.py")


def get_venv_python() -> str:
    if platform.system() == "Windows":
        return os.path.join(VENV_DIR, "Scripts", "python.exe")
    return os.path.join(VENV_DIR, "bin", "python")


def start():
    python = get_venv_python() if os.path.isfile(get_venv_python()) else sys.executable

    # Start the server as a subprocess
    proc = subprocess.Popen(
        [python, MAIN_SCRIPT],
        cwd=ROOT_DIR,
    )

    # Write PID so --stop can find it later
    with open(PID_FILE, "w") as f:
        f.write(str(proc.pid))

    # Wait for the process (keeps this launcher alive while server runs)
    sys.exit(proc.wait())


def stop():
    if not os.path.isfile(PID_FILE):
        return

    with open(PID_FILE, "r") as f:
        pid = int(f.read().strip())

    if platform.system() == "Windows":
        # Kill the entire process tree on Windows
        subprocess.call(
            ["taskkill", "/F", "/T", "/PID", str(pid)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    else:
        import signal
        try:
            os.killpg(os.getpgid(pid), signal.SIGTERM)
        except (ProcessLookupError, PermissionError):
            pass

    if os.path.isfile(PID_FILE):
        os.remove(PID_FILE)


if __name__ == "__main__":
    if "--stop" in sys.argv:
        stop()
    else:
        start()
```

**Key points:**
- When launched normally (no args): starts the server, writes its PID to `.server.pid`, stays alive
- When launched with `--stop`: reads the PID file, kills the process tree, deletes the PID file, exits
- On Windows uses `taskkill /F /T /PID` to kill the entire process tree (server + all children)
- On macOS/Linux uses `os.killpg()` to kill the process group
- Add `.server.pid` to the tracked app's `.gitignore`

## Configuration

All app entries are stored in `config.json` at the project root:

```json
{
  "apps": [
    {
      "uid": "…",
      "name": "My App",
      "frontend_url": "http://localhost:5173/",
      "backend_url": "http://localhost:8000/",
      "project_folder": "C:/Projects/my-app",
      "github_repo": "https://github.com/user/my-app"
    }
  ]
}
```
