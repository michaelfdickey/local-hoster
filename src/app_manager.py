"""
app_manager.py - Backend logic for managing tracked web applications.

Handles:
  - Loading / saving app configs from config.json
  - Starting / stopping / resetting apps via their launcher scripts
  - Exposing a list model to QML
  - Detecting launcher.py (Windows) / launcher.sh (macOS/Linux)
"""

import json
import os
import platform
import subprocess
import uuid
from typing import Optional

from PySide6.QtCore import (
    QObject,
    Signal,
    Slot,
    Property,
    QAbstractListModel,
    QModelIndex,
    Qt,
    QProcess,
    QUrl,
)


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(ROOT_DIR, "config.json")


def _default_launcher_name() -> str:
    """Return the expected launcher script name for the current OS."""
    if platform.system() == "Darwin":
        return "launcher.sh"
    if platform.system() == "Linux":
        return "launcher.sh"
    return "launcher.py"


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
        # Runtime – not persisted
        self.process: Optional[QProcess] = None
        self.running: bool = False
        self.has_launcher: bool = False

    def detect_launcher(self) -> None:
        """Check whether the project folder contains a launcher script."""
        if not self.project_folder or not os.path.isdir(self.project_folder):
            self.has_launcher = False
            return
        launcher = os.path.join(self.project_folder, _default_launcher_name())
        self.has_launcher = os.path.isfile(launcher)

    def launcher_path(self) -> str:
        return os.path.join(self.project_folder, _default_launcher_name())

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

    # -- Properties ----------------------------------------------------------

    @Property(QObject, constant=True)
    def apps(self):
        return self._model

    # -- Config persistence --------------------------------------------------

    def _load_config(self) -> None:
        if not os.path.isfile(CONFIG_PATH):
            return
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        entries = [AppEntry.from_dict(d) for d in data.get("apps", [])]
        self._model.set_entries(entries)
        self.appsChanged.emit()

    def _save_config(self) -> None:
        data = {"apps": [e.to_dict() for e in self._model._entries]}
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    # -- Slots called from QML -----------------------------------------------

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

        # Determine how to invoke the launcher
        if launcher.endswith(".py"):
            # Use python from a venv if available, else system python
            venv_python = os.path.join(entry.project_folder, "venv", "Scripts", "python.exe") \
                if platform.system() == "Windows" \
                else os.path.join(entry.project_folder, "venv", "bin", "python")
            python = venv_python if os.path.isfile(venv_python) else "python"
            proc.start(python, [launcher])
        else:
            # .sh launcher
            proc.start("bash", [launcher])

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
                python = venv_python if os.path.isfile(venv_python) else "python"
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
        entry.running = False
        entry.process = None
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
        """Check if a folder contains the expected launcher script."""
        if not folder or not os.path.isdir(folder):
            return False
        launcher = os.path.join(folder, _default_launcher_name())
        return os.path.isfile(launcher)

    @Slot(result=str)
    def launcherScriptName(self):
        return _default_launcher_name()

    # -- Internal ------------------------------------------------------------

    def _on_process_finished(self, index: int):
        entry = self._model.entry_at(index)
        if entry:
            entry.running = False
            entry.process = None
            self._model.notify_change(index)
