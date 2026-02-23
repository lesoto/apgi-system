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


def analyze_dependencies(file_path: str, exclude_modules: Optional[Set[str]] = None) -> Set[str]:
    """Analyze dependencies from a Python file.

    Parameters
    ----------
    file_path : str
        Path to Python file to analyze
    exclude_modules : Set[str], optional
        Modules to exclude from analysis

    Returns
    -------
    Set[str]
        Set of top-level module dependencies
    """
    if exclude_modules is None:
        exclude_modules = set()

    dependencies = set()

    try:
        import ast

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        tree = ast.parse(content, filename=file_path)

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    # Get top-level module
                    module = alias.name.split(".")[0]
                    if module and module not in exclude_modules:
                        dependencies.add(module)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    # Get top-level module
                    module = node.module.split(".")[0]
                    if module and module not in exclude_modules:
                        dependencies.add(module)

    except (SyntaxError, FileNotFoundError, UnicodeDecodeError):
        # Return empty set on any parsing error
        pass

    return dependencies


def collect_resources(
    project_path: str, patterns: Optional[List[str]] = None
) -> List[tuple[str, str]]:
    """Collect resources from a directory.

    Parameters
    ----------
    project_path : str
        Path to directory to collect from
    patterns : List[str], optional
        File patterns to include, e.g. ["*.yaml", "*.yml"]

    Returns
    -------
    List[tuple[str, str]]
        List of (source_path, dest_path) tuples
    """
    from fnmatch import fnmatch

    project_path_obj = Path(project_path)
    resources: List[tuple[str, str]] = []

    if not project_path_obj.exists() or not project_path_obj.is_dir():
        return resources

    # Default patterns if none provided
    if patterns is None:
        patterns = ["*.yaml", "*.yml", "*.json", "*.png", "*.ico", "*.csv", "*.txt"]

    for pattern in patterns:
        for file_path in project_path_obj.rglob("*"):
            if file_path.is_file() and fnmatch(file_path.name, pattern):
                try:
                    # Make destination relative to project root
                    rel_path = file_path.relative_to(project_path_obj)
                    dest_path = str(rel_path)
                    source_path = str(file_path)
                    resources.append((source_path, dest_path))
                except ValueError:
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
            import toml  # type: ignore

            config = toml.load(pyproject_file)
            return config.get("project", {}).get("version", "0.1.0")
        except ImportError:
            pass

    return "0.1.0"


def detect_hidden_imports(package: str) -> List[str]:
    """Detect hidden imports for a specific package.

    Parameters
    ----------
    package : str
        Package name to get hidden imports for

    Returns
    -------
    List[str]
        List of hidden imports for the package
    """
    # Known hidden imports for common packages
    hidden_imports_map = {
        "scipy": [
            "scipy._lib.messagestream",
            "scipy.special._ufuncs_cxx",
            "scipy.linalg.cython_lapack",
            "scipy.linalg.cython_blas",
        ],
        "matplotlib": [
            "matplotlib.backends._backend_agg",
            "matplotlib.backends._backend_tk",
            "matplotlib.backends.backend_qt5agg",
            "matplotlib.backends.backend_qt4agg",
        ],
        "tkinter": [
            "tkinter.ttk",
            "tkinter.filedialog",
            "tkinter.messagebox",
            "tkinter.simpledialog",
        ],
        "numpy": [
            "numpy.linalg.lapack_lite",
            "numpy.linalg._umath_lapack",
            "numpy.core._multiarray_umath",
        ],
        "sklearn": [
            "sklearn.utils._cython_blas",
            "sklearn.utils._openmp_helpers",
        ],
        "torch": [
            "torch._C",
            "torch._C._dynamo",
        ],
        "jax": [
            "jaxlib.xla_extension",
        ],
    }

    return hidden_imports_map.get(package, [])


# Alias for backward compatibility
get_hidden_imports = detect_hidden_imports


def should_exclude_module(module_name: str, custom_exclusions: Optional[Set[str]] = None) -> bool:
    """Check if a module should be excluded from packaging.

    Parameters
    ----------
    module_name : str
        Module name to check
    custom_exclusions : Set[str], optional
        Custom modules to exclude (if provided, only these are used)

    Returns
    -------
    bool
        True if module should be excluded
    """
    if custom_exclusions is not None:
        exclusions = custom_exclusions
    else:
        # Common exclusions
        exclusions = {
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
            "hypothesis",
        }

    return any(excl in module_name.lower() for excl in exclusions)


def get_excluded_modules() -> Set[str]:
    """Get list of commonly excluded modules.

    Returns
    -------
    Set[str]
        Set of excluded modules
    """
    return {
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
        "hypothesis",
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
    }
