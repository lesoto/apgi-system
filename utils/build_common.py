"""
Build utilities for the APGI system.

This module provides common build and development utilities.
"""

import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional


def run_command(
    cmd: List[str], cwd: Optional[str] = None, check: bool = True
) -> subprocess.CompletedProcess:
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


def analyze_dependencies(project_path: Optional[str] = None) -> Dict[str, Any]:
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
        project_root = get_project_root()
    else:
        project_root = Path(project_path)

    # Read requirements.txt if exists
    requirements_file = project_root / "requirements.txt"
    dependencies = set()

    if requirements_file.exists():
        with open(requirements_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    dependencies.add(line)

    # Read pyproject.toml if exists
    pyproject_file = project_root / "pyproject.toml"
    pyproject_deps = set()

    if pyproject_file.exists():
        try:
            import toml  # type: ignore

            config = toml.load(pyproject_file)
            pyproject_deps = set(config.get("project", {}).get("dependencies", []))
        except ImportError:
            pass

    return {
        "requirements_txt": dependencies,
        "pyproject_toml": pyproject_deps,
        "total_dependencies": len(dependencies) + len(pyproject_deps),
    }


def collect_resources(
    project_path: Optional[str] = None, resource_dirs: Optional[List[str]] = None
) -> Dict[str, List[str]]:
    """Collect project resources.

    Parameters
    ----------
    project_path : str, optional
        Path to project, by default None (current directory)
    resource_dirs : List[str], optional
        List of directory names to collect resources from, by default None (all directories)

    Returns
    -------
    Dict[str, List[str]]
        Resource files by type
    """
    if project_path is None:
        project_root = get_project_root()
    else:
        project_root = Path(project_path)

    resources: Dict[str, List[str]] = {
        "config_files": [],
        "data_files": [],
        "resource_files": [],
        "icon_files": [],
    }

    if resource_dirs is not None:
        for dir_name in resource_dirs:
            dir_path = project_root / dir_name
            if dir_path.exists() and dir_path.is_dir():
                for pattern in ["*.yaml", "*.yml", "*.json", "*.toml", "*.ini"]:
                    resources["config_files"].extend(
                        str(p.relative_to(project_root)) for p in dir_path.rglob(pattern)
                    )
                for pattern in ["*.csv", "*.txt", "*.md"]:
                    resources["data_files"].extend(
                        str(p.relative_to(project_root)) for p in dir_path.rglob(pattern)
                    )
                resources["resource_files"].extend(
                    str(p.relative_to(project_root)) for p in dir_path.rglob("*")
                )
                for pattern in ["*.ico", "*.icns", "*.png", "*.jpg"]:
                    resources["icon_files"].extend(
                        str(p.relative_to(project_root)) for p in dir_path.rglob(pattern)
                    )
    else:
        for pattern in ["*.yaml", "*.yml", "*.json", "*.toml", "*.ini"]:
            resources["config_files"].extend(
                str(p.relative_to(project_root)) for p in project_root.rglob(pattern)
            )
        for pattern in ["*.csv", "*.txt", "*.md"]:
            resources["data_files"].extend(
                str(p.relative_to(project_root)) for p in project_root.rglob(pattern)
            )
        resources_dir = project_root / "resources"
        if resources_dir.exists():
            resources["resource_files"] = [
                str(p.relative_to(project_root)) for p in resources_dir.rglob("*")
            ]
        for pattern in ["*.ico", "*.icns", "*.png", "*.jpg"]:
            resources["icon_files"].extend(
                str(p.relative_to(project_root)) for p in project_root.rglob(pattern)
            )

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
        project_root = get_project_root()
    else:
        project_root = Path(project_path)

    # Try VERSION file
    version_file = project_root / "VERSION"
    if version_file.exists():
        return version_file.read_text().strip()

    # Try pyproject.toml
    pyproject_file = project_root / "pyproject.toml"
    if pyproject_file.exists():
        try:
            import toml

            config = toml.load(pyproject_file)
            version: str = config.get("project", {}).get("version", "0.1.0")
            return version
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
        project_root = get_project_root()
    else:
        project_root = Path(project_path)

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
    python_files = list(project_root.rglob("*.py"))

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
