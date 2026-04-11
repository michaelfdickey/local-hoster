#!/usr/bin/env python3
"""
launcher.py - Local Hoster Application Launcher

Sets up a Python virtual environment (if needed), installs dependencies,
and launches the Local Hoster desktop application.

Usage:
    python launcher.py

On first run this will:
  1. Create a virtual environment in ./venv
  2. Install dependencies from requirements.txt
  3. Launch the app

On subsequent runs it skips straight to step 3.
"""

import os
import sys
import subprocess
import platform


ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
VENV_DIR = os.path.join(ROOT_DIR, "venv")
REQUIREMENTS = os.path.join(ROOT_DIR, "requirements.txt")
MAIN_SCRIPT = os.path.join(ROOT_DIR, "src", "main.py")


def get_venv_python() -> str:
    """Return the path to the Python interpreter inside the venv."""
    if platform.system() == "Windows":
        return os.path.join(VENV_DIR, "Scripts", "python.exe")
    return os.path.join(VENV_DIR, "bin", "python")


def get_venv_pip() -> str:
    """Return the path to pip inside the venv."""
    if platform.system() == "Windows":
        return os.path.join(VENV_DIR, "Scripts", "pip.exe")
    return os.path.join(VENV_DIR, "bin", "pip")


def create_venv() -> None:
    """Create a virtual environment if it does not already exist."""
    if os.path.isdir(VENV_DIR):
        return
    print("[launcher] Creating virtual environment …")
    subprocess.check_call([sys.executable, "-m", "venv", VENV_DIR])
    print("[launcher] Virtual environment created.")


def install_dependencies() -> None:
    """Install/upgrade dependencies from requirements.txt."""
    pip = get_venv_pip()
    print("[launcher] Installing dependencies …")
    subprocess.check_call([pip, "install", "--upgrade", "pip"],
                          stdout=subprocess.DEVNULL)
    subprocess.check_call([pip, "install", "-r", REQUIREMENTS])
    print("[launcher] Dependencies installed.")


def venv_needs_install() -> bool:
    """Check whether site-packages look populated (simple heuristic)."""
    python = get_venv_python()
    if not os.path.isfile(python):
        return True
    # Quick check: can we import PySide6?
    result = subprocess.run(
        [python, "-c", "import PySide6"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return result.returncode != 0


def launch_app() -> None:
    """Launch the main application inside the venv."""
    python = get_venv_python()
    print("[launcher] Starting Local Hoster …")
    sys.exit(subprocess.call([python, MAIN_SCRIPT]))


def main() -> None:
    create_venv()
    if venv_needs_install():
        install_dependencies()
    launch_app()


if __name__ == "__main__":
    main()
