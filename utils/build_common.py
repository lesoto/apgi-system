"""
Build utilities for the APGI system.

This module provides common build and development utilities.
"""

import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional, Set, TypedDict


class Dependencies(TypedDict):
    requirements_txt: Set[str]
    pyproject_toml: Set[str]
    total_dependencies: int


def run_command(
    cmd: List[str], cwd: Optional[str] = None, check: bool = True
) -> subprocess.CompletedProcess[str]:
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


def analyze_dependencies(entry_point: Optional[str] = None) -> Dependencies:
    """Analyze project dependencies from requirements.txt and pyproject.toml.

    Parameters
    ----------
    entry_point : str, optional
        Path to Python entry point file to analyze, by default None (apgi_gui.py)

    Returns
    -------
    dict
        Dictionary with keys: requirements_txt, pyproject_toml, total_dependencies
    """
    project_root = get_project_root()

    dependencies: Dependencies = {
        "requirements_txt": set(),
        "pyproject_toml": set(),
        "total_dependencies": 0,
    }

    # Analyze requirements.txt
    requirements_file = project_root / "requirements.txt"
    if requirements_file.exists():
        try:
            content = requirements_file.read_text()
            for line in content.splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    # Extract package name (before ==, >=, etc.)
                    package = (
                        line.split()[0].split("==")[0].split(">=")[0].split("<=")[0].split("!=")[0]
                    )
                    if package:
                        dependencies["requirements_txt"].add(package)
        except Exception:
            pass

    # Analyze pyproject.toml
    pyproject_file = project_root / "pyproject.toml"
    if pyproject_file.exists():
        try:
            import toml  # type: ignore[import-untyped]

            config = toml.load(pyproject_file)
            deps = config.get("project", {}).get("dependencies", [])
            for dep in deps:
                # Extract package name
                package = dep.split()[0].split("==")[0].split(">=")[0].split("<=")[0].split("!=")[0]
                if package:
                    dependencies["pyproject_toml"].add(package)
        except Exception:
            pass

    # Calculate total unique dependencies
    all_deps = dependencies["requirements_txt"] | dependencies["pyproject_toml"]
    dependencies["total_dependencies"] = len(all_deps)

    return dependencies


def collect_resources(
    project_path: Optional[str] = None, resource_dirs: Optional[List[str]] = None
) -> Dict[str, List[str]]:
    """Collect project resources from specified directories.

    Parameters
    ----------
    project_path : str, optional
        Path to project, by default None (current directory)
    resource_dirs : List[str], optional
        List of directory names to collect from, by default None (all)

    Returns
    -------
    dict
        Dictionary with keys: config_files, data_files, resource_files, icon_files
    """
    if project_path is None:
        project_path_obj = get_project_root()
    else:
        project_path_obj = Path(project_path)

    resources: Dict[str, List[str]] = {
        "config_files": [],
        "data_files": [],
        "resource_files": [],
        "icon_files": [],
    }

    # If no specific directories provided, use defaults
    if resource_dirs is None:
        resource_dirs = ["config", "resources"]

    # Collect from each specified directory
    for dir_name in resource_dirs:
        dir_path = project_path_obj / dir_name
        if dir_path.exists() and dir_path.is_dir():
            # Collect all files in this directory recursively
            for file_path in dir_path.rglob("*"):
                if file_path.is_file():
                    # Create relative destination path
                    try:
                        rel_path = file_path.relative_to(project_path_obj)
                        file_str = str(rel_path)

                        # Categorize files
                        if dir_name == "config":
                            resources["config_files"].append(file_str)
                        elif dir_name == "resources":
                            if file_path.suffix in [".ico", ".icns", ".png"]:
                                resources["icon_files"].append(file_str)
                            else:
                                resources["resource_files"].append(file_str)
                        else:
                            resources["data_files"].append(file_str)

                    except ValueError:
                        # File not under project root, skip
                        continue

    return resources


def get_version(project_path: Optional[str] = None) -> str:
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
        project_path_obj = get_project_root()
    else:
        project_path_obj = Path(project_path)

    # Try VERSION file
    version_file = project_path_obj / "VERSION"
    if version_file.exists():
        return version_file.read_text().strip()

    # Try pyproject.toml
    pyproject_file = project_path_obj / "pyproject.toml"
    if pyproject_file.exists():
        try:
            import toml

            config = toml.load(pyproject_file)
            return config.get("project", {}).get("version", "0.1.0")
        except ImportError:
            pass

    return "0.1.0"


def detect_hidden_imports(project_path: Optional[str] = None) -> List[str]:
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
        project_path_obj = get_project_root()
    else:
        project_path_obj = Path(project_path)

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
    python_files = list(project_path_obj.rglob("*.py"))

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
