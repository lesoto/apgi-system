"""
Cross-platform utilities for resource loading and platform detection.

This module provides platform-agnostic functions for:
- Detecting the current operating system
- Determining if running as a bundled executable
- Resolving resource paths in both development and bundled environments
- Getting platform-appropriate directories for user-writable data
"""

import os
import sys
import platform
from pathlib import Path
from typing import Optional


def get_platform() -> str:
    """
    Get current platform identifier.

    Returns:
        'windows', 'macos', or 'linux'
    """
    system = platform.system().lower()

    if system == "windows":
        return "windows"
    elif system == "darwin":
        return "macos"
    elif system == "linux":
        return "linux"
    else:
        return "unknown"


def is_bundled() -> bool:
    """
    Check if running as bundled executable.

    PyInstaller sets sys.frozen and sys._MEIPASS when running as executable.
    py2app sets sys.frozen when running as .app bundle.

    Returns:
        True if bundled, False if running from source
    """
    return getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")


def get_resource_path(relative_path: str) -> Path:
    """
    Get absolute path to resource, works for dev and bundled environments.

    In development: returns path relative to project root
    In bundled executable: returns path relative to temporary extraction directory

    Args:
        relative_path: Path relative to application root (e.g., 'config/default.yaml')

    Returns:
        Absolute path to resource

    Example:
        >>> config_path = get_resource_path('config/default.yaml')
        >>> with open(config_path) as f:
        ...     config = yaml.safe_load(f)
    """
    if is_bundled():
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = Path(sys._MEIPASS)
    else:
        # Running from source - use project root
        # This file is in apgi_system/, so go up one level
        base_path = Path(__file__).parent.parent

    return base_path / relative_path


def get_config_dir() -> Path:
    """
    Get platform-appropriate configuration directory.

    Returns user-writable directory for storing configuration files.
    Creates the directory if it doesn't exist.

    Returns:
        Path to config directory (user-writable)

    Platform-specific locations:
        - Windows: %APPDATA%/APGI System/
        - macOS: ~/Library/Application Support/APGI System/
        - Linux: ~/.config/apgi-system/
    """
    app_name = "APGI System"
    current_platform = get_platform()

    if current_platform == "windows":
        # Use APPDATA on Windows
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
        config_dir = base / app_name
    elif current_platform == "macos":
        # Use Application Support on macOS
        config_dir = Path.home() / "Library" / "Application Support" / app_name
    else:
        # Use XDG config directory on Linux
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
        config_dir = base / "apgi-system"

    # Create directory if it doesn't exist
    config_dir.mkdir(parents=True, exist_ok=True)

    return config_dir


def get_data_dir() -> Path:
    """
    Get platform-appropriate data directory.

    Returns user-writable directory for storing application data files.
    Creates the directory if it doesn't exist.

    Returns:
        Path to data directory (user-writable)

    Platform-specific locations:
        - Windows: %LOCALAPPDATA%/APGI System/
        - macOS: ~/Library/Application Support/APGI System/Data/
        - Linux: ~/.local/share/apgi-system/
    """
    app_name = "APGI System"
    current_platform = get_platform()

    if current_platform == "windows":
        # Use LOCALAPPDATA on Windows
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        data_dir = base / app_name
    elif current_platform == "macos":
        # Use Application Support/Data on macOS
        data_dir = Path.home() / "Library" / "Application Support" / app_name / "Data"
    else:
        # Use XDG data directory on Linux
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
        data_dir = base / "apgi-system"

    # Create directory if it doesn't exist
    data_dir.mkdir(parents=True, exist_ok=True)

    return data_dir


def get_base_path() -> Path:
    """
    Get the base path of the application.

    Returns:
        Path to application base directory
    """
    if is_bundled():
        return Path(sys._MEIPASS)
    else:
        return Path(__file__).parent.parent
