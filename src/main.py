"""
main.py - Entry point for the Local Hoster desktop application.

Registers Python-side QML types and loads the QML UI.
"""

import sys
import os
import signal

# Force the Basic style so custom QML backgrounds/contentItems work on all OS
os.environ["QT_QUICK_CONTROLS_STYLE"] = "Basic"

from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

# Ensure the src package is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app_manager import AppManager  # noqa: E402


def main() -> None:
    # Allow Ctrl-C from terminal to kill the app
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    app = QGuiApplication(sys.argv)
    app.setApplicationName("Local Hoster")
    app.setOrganizationName("LocalHoster")

    engine = QQmlApplicationEngine()

    # Expose the backend model to QML
    manager = AppManager()
    engine.rootContext().setContextProperty("appManager", manager)

    qml_file = os.path.join(os.path.dirname(__file__), "qml", "Main.qml")
    engine.load(qml_file)

    if not engine.rootObjects():
        print("[error] Failed to load QML. Exiting.")
        sys.exit(1)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
