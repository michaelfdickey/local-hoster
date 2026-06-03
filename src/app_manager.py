"""
app_manager.py - Backend logic for managing tracked web applications.

Handles:
  - Loading / saving app configs from config.json
  - Starting / stopping / resetting apps via their launcher scripts
  - Exposing a list model to QML
  - Detecting launcher.py or launcher.sh in project folders
  - Extracting ports from frontend/backend URLs and passing them to launchers
  - Detecting whether apps are already running by checking port usage
"""

import json
import os
import platform
import socket
import subprocess
import sys
import uuid
from typing import Optional
from urllib.parse import urlparse

from PySide6.QtCore import (
    QObject,
    Signal,
    Slot,
    Property,
    QAbstractListModel,
    QModelIndex,
    Qt,
    QProcess,
    QTimer,
    QUrl,
)


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(ROOT_DIR, "config.json")

# Launcher script names to look for, in priority order
LAUNCHER_NAMES = ["launcher.sh", "launcher.py"]


def _find_launcher(project_folder: str) -> Optional[str]:
    """Return the first launcher script found in the project folder, or None."""
    if not project_folder or not os.path.isdir(project_folder):
        return None
    for name in LAUNCHER_NAMES:
        path = os.path.join(project_folder, name)
        if os.path.isfile(path):
            return name
    return None


def _extract_port(url: str) -> Optional[int]:
    """Extract the port number from a URL string, or None if absent."""
    if not url:
        return None
    try:
        parsed = urlparse(url)
        if parsed.port:
            return parsed.port
    except Exception:
        pass
    return None


def _is_port_in_use(port: int) -> bool:
    """Check whether a TCP port is currently in use on localhost."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.3)
            return s.connect_ex(("127.0.0.1", port)) == 0
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Data container
# ---------------------------------------------------------------------------

class AppEntry:
    """Plain data object representing one tracked application."""

    def __init__(
        self,
        uid: str = "",
        name: str = "",
        frontend_url: str = "",
        backend_url: str = "",
        project_folder: str = "",
        github_repo: str = "",
    ):
        self.uid: str = uid or str(uuid.uuid4())
        self.name: str = name
        self.frontend_url: str = frontend_url
        self.backend_url: str = backend_url
        self.project_folder: str = project_folder
        self.github_repo: str = github_repo
        # Runtime state (not persisted)
        self.process: Optional[QProcess] = None
        self.running: bool = False
        self.has_launcher: bool = False
        self._launcher_name: Optional[str] = None

    def detect_launcher(self) -> None:
        """Check whether the project folder contains a launcher script."""
        self._launcher_name = _find_launcher(self.project_folder)
        self.has_launcher = self._launcher_name is not None

    def launcher_path(self) -> str:
        if self._launcher_name:
            return os.path.join(self.project_folder, self._launcher_name)
        return ""

    @property
    def frontend_port(self) -> Optional[int]:
        return _extract_port(self.frontend_url)

    @property
    def backend_port(self) -> Optional[int]:
        return _extract_port(self.backend_url)

    def check_running_by_port(self) -> bool:
        """Return True if either the frontend or backend port is in use."""
        fp = self.frontend_port
        bp = self.backend_port
        if fp and _is_port_in_use(fp):
            return True
        if bp and _is_port_in_use(bp):
            return True
        return False

    def to_dict(self) -> dict:
        return {
            "uid": self.uid,
            "name": self.name,
            "frontend_url": self.frontend_url,
            "backend_url": self.backend_url,
            "project_folder": self.project_folder,
            "github_repo": self.github_repo,
        }

    @staticmethod
    def from_dict(d: dict) -> "AppEntry":
        entry = AppEntry(
            uid=d.get("uid", ""),
            name=d.get("name", ""),
            frontend_url=d.get("frontend_url", ""),
            backend_url=d.get("backend_url", ""),
            project_folder=d.get("project_folder", ""),
            github_repo=d.get("github_repo", ""),
        )
        entry.detect_launcher()
        return entry


# ---------------------------------------------------------------------------
# Qt List Model
# ---------------------------------------------------------------------------

class AppListModel(QAbstractListModel):
    """Exposes AppEntry objects to QML as a list model."""

    NameRole = Qt.UserRole + 1
    FrontendUrlRole = Qt.UserRole + 2
    BackendUrlRole = Qt.UserRole + 3
    ProjectFolderRole = Qt.UserRole + 4
    GithubRepoRole = Qt.UserRole + 5
    RunningRole = Qt.UserRole + 6
    HasLauncherRole = Qt.UserRole + 7
    UidRole = Qt.UserRole + 8

    def __init__(self, parent=None):
        super().__init__(parent)
        self._entries: list[AppEntry] = []

    # -- required overrides --------------------------------------------------

    def rowCount(self, parent=QModelIndex()):
        return len(self._entries)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or index.row() >= len(self._entries):
            return None
        entry = self._entries[index.row()]
        if role == self.NameRole:
            return entry.name
        if role == self.FrontendUrlRole:
            return entry.frontend_url
        if role == self.BackendUrlRole:
            return entry.backend_url
        if role == self.ProjectFolderRole:
            return entry.project_folder
        if role == self.GithubRepoRole:
            return entry.github_repo
        if role == self.RunningRole:
            return entry.running
        if role == self.HasLauncherRole:
            return entry.has_launcher
        if role == self.UidRole:
            return entry.uid
        return None

    def roleNames(self):
        return {
            self.NameRole: b"name",
            self.FrontendUrlRole: b"frontendUrl",
            self.BackendUrlRole: b"backendUrl",
            self.ProjectFolderRole: b"projectFolder",
            self.GithubRepoRole: b"githubRepo",
            self.RunningRole: b"running",
            self.HasLauncherRole: b"hasLauncher",
            self.UidRole: b"uid",
        }

    # -- helpers -------------------------------------------------------------

    def set_entries(self, entries: list[AppEntry]):
        self.beginResetModel()
        self._entries = entries
        self.endResetModel()

    def append(self, entry: AppEntry):
        row = len(self._entries)
        self.beginInsertRows(QModelIndex(), row, row)
        self._entries.append(entry)
        self.endInsertRows()

    def remove(self, row: int):
        if 0 <= row < len(self._entries):
            self.beginRemoveRows(QModelIndex(), row, row)
            self._entries.pop(row)
            self.endRemoveRows()

    def entry_at(self, row: int) -> Optional[AppEntry]:
        if 0 <= row < len(self._entries):
            return self._entries[row]
        return None

    def notify_change(self, row: int):
        """Emit dataChanged for a single row."""
        idx = self.index(row, 0)
        self.dataChanged.emit(idx, idx, self.roleNames().keys())


# ---------------------------------------------------------------------------
# App Manager  (the main backend object exposed to QML)
# ---------------------------------------------------------------------------

class AppManager(QObject):
    """
    Central controller exposed to QML via a context property.

    Responsibilities:
      - CRUD operations on tracked apps
      - Persist to / load from config.json
      - Start / stop / reset app processes
    """

    appsChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._model = AppListModel(self)
        self._load_config()
        # Periodically check if apps are running by probing their ports
        self._poll_timer = QTimer(self)
        self._poll_timer.setInterval(5000)  # every 5 seconds
        self._poll_timer.timeout.connect(self._poll_running_status)
        self._poll_timer.start()

    # -- Properties ----------------------------------------------------------

    @Property(QObject, constant=True)
    def apps(self):
        return self._model

    # -- Config persistence --------------------------------------------------

    def _load_config(self) -> None:
        if not os.path.isfile(CONFIG_PATH):
            return
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            print(f"[warn] Failed to load config: {e}")
            return
        entries = [AppEntry.from_dict(d) for d in data.get("apps", [])]
        # Detect which apps are already running by checking their ports
        for entry in entries:
            if entry.check_running_by_port():
                entry.running = True
        self._model.set_entries(entries)
        self.appsChanged.emit()

    def _save_config(self) -> None:
        data = {"apps": [e.to_dict() for e in self._model._entries]}
        try:
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except OSError as e:
            print(f"[warn] Failed to save config: {e}")

    # -- Slots called from QML -----------------------------------------------

    @Slot(str, bool)
    def sortApps(self, column: str, ascending: bool):
        """Sort the app list by the given column name."""
        key_map = {
            "name": lambda e: (e.name or "").lower(),
            "frontend": lambda e: (e.frontend_url or "").lower(),
            "status": lambda e: (0 if e.running else 1),  # Running first when ascending
        }
        key_fn = key_map.get(column)
        if key_fn is None:
            return
        self._model.beginResetModel()
        self._model._entries.sort(key=key_fn, reverse=not ascending)
        self._model.endResetModel()

    @Slot(str, str, str, str, str)
    def addApp(self, name, frontend_url, backend_url, project_folder, github_repo):
        """Add a new tracked application."""
        entry = AppEntry(
            name=name,
            frontend_url=frontend_url,
            backend_url=backend_url,
            project_folder=project_folder,
            github_repo=github_repo,
        )
        entry.detect_launcher()
        self._model.append(entry)
        self._save_config()
        self.appsChanged.emit()

    @Slot(int, str, str, str, str, str)
    def updateApp(self, index, name, frontend_url, backend_url, project_folder, github_repo):
        """Update an existing tracked application."""
        entry = self._model.entry_at(index)
        if entry is None:
            return
        entry.name = name
        entry.frontend_url = frontend_url
        entry.backend_url = backend_url
        entry.project_folder = project_folder
        entry.github_repo = github_repo
        entry.detect_launcher()
        self._model.notify_change(index)
        self._save_config()
        self.appsChanged.emit()

    @Slot(int)
    def removeApp(self, index):
        entry = self._model.entry_at(index)
        if entry and entry.process and entry.process.state() != QProcess.NotRunning:
            entry.process.kill()
            entry.process.waitForFinished(3000)
        self._model.remove(index)
        self._save_config()
        self.appsChanged.emit()

    @Slot(int)
    def startApp(self, index):
        entry = self._model.entry_at(index)
        if entry is None or entry.running:
            return
        if not entry.has_launcher:
            print(f"[warn] No launcher script found for '{entry.name}'")
            return

        launcher = entry.launcher_path()
        proc = QProcess(self)
        proc.setWorkingDirectory(entry.project_folder)

        # Build port arguments
        extra_args = []
        if entry.frontend_port:
            extra_args += ["-p", str(entry.frontend_port)]
        if entry.backend_port:
            extra_args += ["-b", str(entry.backend_port)]

        # Determine how to invoke the launcher
        if launcher.endswith(".py"):
            # Use python from a venv if available, else system python
            venv_python = os.path.join(entry.project_folder, "venv", "Scripts", "python.exe") \
                if platform.system() == "Windows" \
                else os.path.join(entry.project_folder, "venv", "bin", "python")
            python = venv_python if os.path.isfile(venv_python) else sys.executable
            proc.start(python, [launcher] + extra_args)
        else:
            # .sh launcher
            proc.start("bash", [launcher] + extra_args)

        entry.process = proc
        entry.running = True
        self._model.notify_change(index)

        # Track process exit
        proc.finished.connect(lambda _exit_code, _exit_status, idx=index: self._on_process_finished(idx))

    @Slot(int)
    def stopApp(self, index):
        entry = self._model.entry_at(index)
        if entry is None or not entry.running:
            return

        # Invoke the launcher with --stop so it can kill its own child processes
        if entry.has_launcher:
            launcher = entry.launcher_path()
            if launcher.endswith(".py"):
                venv_python = os.path.join(entry.project_folder, "venv", "Scripts", "python.exe") \
                    if platform.system() == "Windows" \
                    else os.path.join(entry.project_folder, "venv", "bin", "python")
                python = venv_python if os.path.isfile(venv_python) else sys.executable
                subprocess.call(
                    [python, launcher, "--stop"],
                    cwd=entry.project_folder,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=10,
                )
            else:
                subprocess.call(
                    ["bash", launcher, "--stop"],
                    cwd=entry.project_folder,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=10,
                )

        # Clean up the QProcess handle
        if entry.process:
            if entry.process.state() != QProcess.NotRunning:
                entry.process.kill()
                entry.process.waitForFinished(3000)
            entry.process = None
        else:
            # No QProcess handle (app was running before Local Hoster started).
            # Kill by port using lsof/kill on macOS/Linux, netstat on Windows.
            self._kill_by_ports(entry)
        entry.running = False
        self._model.notify_change(index)

    @Slot(int)
    def resetApp(self, index):
        """Stop then start the application."""
        self.stopApp(index)
        self.startApp(index)

    @Slot(int, result=str)
    def getAppName(self, index):
        entry = self._model.entry_at(index)
        return entry.name if entry else ""

    @Slot(int, result=str)
    def getAppFrontendUrl(self, index):
        entry = self._model.entry_at(index)
        return entry.frontend_url if entry else ""

    @Slot(int, result=str)
    def getAppBackendUrl(self, index):
        entry = self._model.entry_at(index)
        return entry.backend_url if entry else ""

    @Slot(int, result=str)
    def getAppProjectFolder(self, index):
        entry = self._model.entry_at(index)
        return entry.project_folder if entry else ""

    @Slot(int, result=str)
    def getAppGithubRepo(self, index):
        entry = self._model.entry_at(index)
        return entry.github_repo if entry else ""

    @Slot(str, result=bool)
    def hasLauncherScript(self, folder):
        """Check if a folder contains a launcher script."""
        return _find_launcher(folder) is not None

    @Slot(result=str)
    def launcherScriptName(self):
        return ", ".join(LAUNCHER_NAMES)

    # -- Internal ------------------------------------------------------------

    def _on_process_finished(self, index: int):
        entry = self._model.entry_at(index)
        if entry:
            entry.running = False
            entry.process = None
            self._model.notify_change(index)

    def _poll_running_status(self):
        """Periodically check each app's ports and update running status."""
        for i, entry in enumerate(self._model._entries):
            # If we launched it ourselves, trust the QProcess state
            if entry.process is not None:
                continue
            port_active = entry.check_running_by_port()
            if port_active != entry.running:
                entry.running = port_active
                self._model.notify_change(i)

    @staticmethod
    def _kill_by_ports(entry: "AppEntry") -> None:
        """Attempt to kill processes listening on the app's ports."""
        ports = []
        if entry.frontend_port:
            ports.append(entry.frontend_port)
        if entry.backend_port:
            ports.append(entry.backend_port)
        for port in ports:
            try:
                if platform.system() in ("Darwin", "Linux"):
                    # Use lsof to find PIDs listening on the port
                    result = subprocess.run(
                        ["lsof", "-ti", f"tcp:{port}"],
                        capture_output=True, text=True, timeout=5,
                    )
                    pids = result.stdout.strip().split("\n")
                    for pid in pids:
                        pid = pid.strip()
                        if pid.isdigit():
                            subprocess.run(["kill", pid], timeout=5)
                else:
                    # Windows: use netstat + taskkill
                    result = subprocess.run(
                        ["netstat", "-ano"],
                        capture_output=True, text=True, timeout=5,
                    )
                    for line in result.stdout.splitlines():
                        if f":{port}" in line and "LISTENING" in line:
                            parts = line.split()
                            pid = parts[-1].strip()
                            if pid.isdigit():
                                subprocess.run(
                                    ["taskkill", "/F", "/PID", pid],
                                    timeout=5,
                                )
            except Exception as e:
                print(f"[warn] Failed to kill process on port {port}: {e}")
