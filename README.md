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
