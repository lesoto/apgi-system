"""
Build utilities for the APGI system.

This module provides common build and development utilities.
"""

import os
import subprocess
from pathlib import Path
from typing import List, Dict, Any


def run_command(cmd: List[str], cwd: str = None, check: bool = True) -> subprocess.CompletedProcess:
    """Run a command and return the result.

    Parameters
    ----------
    cmd : List[str]
        Command to run
    cwd : str, optional
        Working directory
    check : bool, optional
        Whether to check return code, by default True

    Returns
    -------
    subprocess.CompletedProcess
        Command result
    """
    return subprocess.run(cmd, cwd=cwd, check=check, capture_output=True, text=True)


def get_project_root() -> Path:
    """Get the project root directory.

    Returns
    -------
    Path
        Project root path
    """
    return Path(__file__).parent.parent


def get_build_config() -> Dict[str, Any]:
    """Get build configuration.

    Returns
    -------
    Dict[str, Any]
        Build configuration
    """
    return {
        "project_name": "apgi-system",
        "version": "0.1.0",
        "python_requires": ">=3.8",
        "dependencies": [
            "numpy",
            "scipy",
            "matplotlib",
            "pandas",
            "sklearn",
            "networkx",
            "torch",
            "jax",
            "fastapi",
            "uvicorn",
            "pydantic",
            "sqlalchemy",
            "redis",
            "psycopg2-binary",
        ],
    }


def check_build_environment() -> Dict[str, bool]:
    """Check if build environment is ready.

    Returns
    -------
    Dict[str, bool]
        Environment check results
    """
    checks = {}

    # Check Python version
    import sys

    checks["python_version"] = sys.version_info >= (3, 8)

    # Check essential tools
    try:
        subprocess.run(["git", "--version"], capture_output=True, check=True)
        checks["git"] = True
    except (subprocess.CalledProcessError, FileNotFoundError):
        checks["git"] = False

    # Check pip
    try:
        subprocess.run(["pip", "--version"], capture_output=True, check=True)
        checks["pip"] = True
    except (subprocess.CalledProcessError, FileNotFoundError):
        checks["pip"] = False

    return checks


def analyze_dependencies(project_path: str = None) -> Dict[str, Any]:
    """Analyze project dependencies.

    Parameters
    ----------
    project_path : str, optional
        Path to project, by default None (current directory)

    Returns
    -------
    Dict[str, Any]
        Dependency analysis results
    """
    if project_path is None:
        project_path = get_project_root()

    project_path = Path(project_path)

    # Read requirements.txt if exists
    requirements_file = project_path / "requirements.txt"
    dependencies = []

    if requirements_file.exists():
        with open(requirements_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    dependencies.append(line)

    # Read pyproject.toml if exists
    pyproject_file = project_path / "pyproject.toml"
    pyproject_deps = []

    if pyproject_file.exists():
        try:
            import toml

            config = toml.load(pyproject_file)
            pyproject_deps = config.get("project", {}).get("dependencies", [])
        except ImportError:
            pass

    return {
        "requirements_txt": dependencies,
        "pyproject_toml": pyproject_deps,
        "total_dependencies": len(dependencies) + len(pyproject_deps),
    }


def collect_resources(project_path: str = None) -> Dict[str, List[str]]:
    """Collect project resources.

    Parameters
    ----------
    project_path : str, optional
        Path to project, by default None (current directory)

    Returns
    -------
    Dict[str, List[str]]
        Resource files by type
    """
    if project_path is None:
        project_path = get_project_root()

    project_path = Path(project_path)
    resources = {"config_files": [], "data_files": [], "resource_files": [], "icon_files": []}

    # Collect config files
    for pattern in ["*.yaml", "*.yml", "*.json", "*.toml", "*.ini"]:
        resources["config_files"].extend(project_path.rglob(pattern))

    # Collect data files
    for pattern in ["*.csv", "*.txt", "*.md"]:
        resources["data_files"].extend(project_path.rglob(pattern))

    # Collect resource files
    resources_dir = project_path / "resources"
    if resources_dir.exists():
        resources["resource_files"] = list(resources_dir.rglob("*"))

    # Collect icon files
    for pattern in ["*.ico", "*.icns", "*.png", "*.jpg"]:
        resources["icon_files"].extend(project_path.rglob(pattern))

    # Convert to strings
    for key in resources:
        resources[key] = [str(p) for p in resources[key]]

    return resources


def get_version(project_path: str = None) -> str:
    """Get project version.

    Parameters
    ----------
    project_path : str, optional
        Path to project, by default None (current directory)

    Returns
    -------
    str
        Project version
    """
    if project_path is None:
        project_path = get_project_root()

    project_path = Path(project_path)

    # Try VERSION file
    version_file = project_path / "VERSION"
    if version_file.exists():
        return version_file.read_text().strip()

    # Try pyproject.toml
    pyproject_file = project_path / "pyproject.toml"
    if pyproject_file.exists():
        try:
            import toml

            config = toml.load(pyproject_file)
            return config.get("project", {}).get("version", "0.1.0")
        except ImportError:
            pass

    return "0.1.0"


def detect_hidden_imports(project_path: str = None) -> List[str]:
    """Detect hidden imports in the project.

    Parameters
    ----------
    project_path : str, optional
        Path to project, by default None (current directory)

    Returns
    -------
    List[str]
        List of hidden imports
    """
    if project_path is None:
        project_path = get_project_root()

    project_path = Path(project_path)
    hidden_imports = []

    # Common hidden imports for scientific packages
    common_hidden = [
        "numpy.linalg.lapack_lite",
        "numpy.linalg.umath_lapack",
        "scipy.special._ufuncs_cxx",
        "scipy.linalg.cython_lapack",
        "scipy.linalg.cython_blas",
        "sklearn.utils._cython_blas",
        "sklearn.utils._openmp_helpers",
        "torch._C",
        "torch._C._dynamo",
        "jaxlib.xla_extension",
    ]

    # Check if these packages are used
    python_files = list(project_path.rglob("*.py"))

    for py_file in python_files:
        try:
            content = py_file.read_text()
            for hidden in common_hidden:
                package = hidden.split(".")[0]
                if package in content and hidden not in hidden_imports:
                    hidden_imports.append(hidden)
        except Exception:
            continue

    return hidden_imports


# Alias for backward compatibility
get_hidden_imports = detect_hidden_imports


def should_exclude_module(module_name: str) -> bool:
    """Check if a module should be excluded from packaging.

    Parameters
    ----------
    module_name : str
        Module name to check

    Returns
    -------
    bool
        True if module should be excluded
    """
    # Common exclusions
    exclusions = [
        "test",
        "tests",
        "pytest",
        "_pytest",
        "setuptools",
        "pip",
        "wheel",
        "debug",
        "pdb",
        "ipdb",
        "jupyter",
        "ipython",
        "sphinx",
        "docs",
        "examples",
        "samples",
        "mypy",
        "flake8",
        "black",
        "coverage",
        "coveralls",
    ]

    return any(excl in module_name.lower() for excl in exclusions)


def get_excluded_modules() -> List[str]:
    """Get list of commonly excluded modules.

    Returns
    -------
    List[str]
        List of excluded modules
    """
    return [
        "test",
        "tests",
        "pytest",
        "_pytest",
        "setuptools",
        "pip",
        "wheel",
        "debug",
        "pdb",
        "ipdb",
        "jupyter",
        "ipython",
        "sphinx",
        "docs",
        "examples",
        "samples",
        "mypy",
        "flake8",
        "black",
        "coverage",
        "coveralls",
        "tkinter.test",
        "unittest",
        "doctest",
        "argparse",
        "email",
        "html",
        "http",
        "urllib",
        "xml",
        "xmlrpc",
    ]
