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


def analyze_dependencies(
    file_path: str, exclude_modules: Optional[Set[str]] = None
) -> Dependencies:
    """Analyze dependencies from a Python file.

    Parameters
    ----------
    file_path : str
        Path to Python file to analyze
    exclude_modules : Set[str], optional
        Modules to exclude from analysis

    Returns
    -------
    Dependencies
        Dictionary with categorized dependencies
    """
    if exclude_modules is None:
        exclude_modules = set()

    # Standard library modules to exclude
    stdlib_modules = {
        "abc",
        "argparse",
        "array",
        "asyncio",
        "atexit",
        "base64",
        "binascii",
        "bisect",
        "builtins",
        "bytes",
        "calendar",
        "cgi",
        "cgitb",
        "chunk",
        "codecs",
        "collections",
        "colorsys",
        "compileall",
        "concurrent",
        "configparser",
        "contextlib",
        "copy",
        "copyreg",
        "csv",
        "ctypes",
        "curses",
        "dataclasses",
        "datetime",
        "decimal",
        "difflib",
        "dis",
        "doctest",
        "email",
        "enum",
        "errno",
        "faulthandler",
        "fcntl",
        "filecmp",
        "fileinput",
        "fnmatch",
        "formatter",
        "fractions",
        "ftplib",
        "functools",
        "gc",
        "getopt",
        "getpass",
        "gettext",
        "glob",
        "grp",
        "gzip",
        "hashlib",
        "heapq",
        "hmac",
        "html",
        "http",
        "imaplib",
        "imghdr",
        "imp",
        "importlib",
        "inspect",
        "io",
        "ipaddress",
        "itertools",
        "json",
        "keyword",
        "linecache",
        "locale",
        "logging",
        "lzma",
        "mailbox",
        "mailcap",
        "marshal",
        "math",
        "mimetypes",
        "mmap",
        "modulefinder",
        "multiprocessing",
        "netrc",
        "nntplib",
        "numbers",
        "operator",
        "os",
        "ossaudiodev",
        "pathlib",
        "pdb",
        "pickle",
        "pickletools",
        "pipes",
        "pkgutil",
        "platform",
        "plistlib",
        "poplib",
        "posix",
        "pprint",
        "profile",
        "pstats",
        "pty",
        "pwd",
        "py_compile",
        "pyclbr",
        "pydoc",
        "queue",
        "quopri",
        "random",
        "re",
        "readline",
        "reprlib",
        "resource",
        "rlcompleter",
        "runpy",
        "sched",
        "secrets",
        "select",
        "selectors",
        "shelve",
        "shlex",
        "shutil",
        "signal",
        "site",
        "smtpd",
        "smtplib",
        "sndhdr",
        "socket",
        "socketserver",
        "sqlite3",
        "ssl",
        "stat",
        "statistics",
        "string",
        "struct",
        "subprocess",
        "sunau",
        "symbol",
        "symtable",
        "sys",
        "sysconfig",
        "syslog",
        "tabnanny",
        "tarfile",
        "telnetlib",
        "tempfile",
        "termios",
        "textwrap",
        "threading",
        "time",
        "timeit",
        "tkinter",
        "token",
        "tokenize",
        "trace",
        "traceback",
        "tracemalloc",
        "tty",
        "turtle",
        "types",
        "typing",
        "unicodedata",
        "unittest",
        "urllib",
        "uu",
        "uuid",
        "venv",
        "warnings",
        "wave",
        "weakref",
        "webbrowser",
        "winreg",
        "winsound",
        "wsgiref",
        "xdrlib",
        "xml",
        "xmlrpc",
        "zipapp",
        "zipfile",
        "zipimport",
        "zlib",
    }

    # Combine exclude_modules with stdlib_modules
    all_excludes = exclude_modules | stdlib_modules

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
                    if module and module not in all_excludes:
                        dependencies.add(module)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    # Get top-level module
                    module = node.module.split(".")[0]
                    if module and module not in all_excludes:
                        dependencies.add(module)

    except (SyntaxError, FileNotFoundError, UnicodeDecodeError):
        # Return empty dependencies on any parsing error
        dependencies = set()

    # Categorize dependencies
    requirements_txt_deps = set()
    pyproject_toml_deps = set()

    # Common dependencies that are typically in requirements.txt
    requirements_common = {"numpy", "scipy", "matplotlib", "pandas", "sklearn", "networkx"}
    # Dependencies that might be in pyproject.toml
    pyproject_common = {
        "torch",
        "jax",
        "fastapi",
        "uvicorn",
        "pydantic",
        "sqlalchemy",
        "redis",
        "psycopg2-binary",
    }

    for dep in dependencies:
        if dep in requirements_common:
            requirements_txt_deps.add(dep)
        elif dep in pyproject_common:
            pyproject_toml_deps.add(dep)
        else:
            # Default to requirements.txt for unknown dependencies
            requirements_txt_deps.add(dep)

    return {
        "requirements_txt": requirements_txt_deps,
        "pyproject_toml": pyproject_toml_deps,
        "total_dependencies": len(dependencies),
    }


def collect_resources(
    project_path: str, resource_dirs: Optional[List[str]] = None
) -> Dict[str, List[str]]:
    """Collect resources from specified directories.

    Parameters
    ----------
    project_path : str
        Path to project root
    resource_dirs : List[str], optional
        List of directory names to collect from

    Returns
    -------
    Dict[str, List[str]]
        Dictionary with categorized resources
    """
    from pathlib import Path

    project_path_obj = Path(project_path)
    resources = {"config_files": [], "data_files": [], "resource_files": [], "icon_files": []}

    if not project_path_obj.exists() or not project_path_obj.is_dir():
        return resources

    # Default to common directories if none specified
    if resource_dirs is None:
        resource_dirs = ["config", "resources", "data", "icons"]

    # Define file patterns for each category
    config_patterns = ["*.yaml", "*.yml", "*.json", "*.toml", "*.ini"]
    data_patterns = ["*.csv", "*.json", "*.txt", "*.dat"]
    resource_patterns = ["*.png", "*.jpg", "*.jpeg", "*.gif", "*.ico", "*.svg"]
    icon_patterns = ["*.ico", "*.png", "*.icns"]

    for dir_name in resource_dirs:
        dir_path = project_path_obj / dir_name
        if not dir_path.exists() or not dir_path.is_dir():
            continue

        # Collect config files
        for pattern in config_patterns:
            for file_path in dir_path.rglob(pattern):
                if file_path.is_file():
                    try:
                        rel_path = file_path.relative_to(project_path_obj)
                        resources["config_files"].append(str(rel_path))
                    except ValueError:
                        continue

        # Collect data files
        for pattern in data_patterns:
            for file_path in dir_path.rglob(pattern):
                if file_path.is_file():
                    try:
                        rel_path = file_path.relative_to(project_path_obj)
                        resources["data_files"].append(str(rel_path))
                    except ValueError:
                        continue

        # Collect resource files
        for pattern in resource_patterns:
            for file_path in dir_path.rglob(pattern):
                if file_path.is_file():
                    try:
                        rel_path = file_path.relative_to(project_path_obj)
                        resources["resource_files"].append(str(rel_path))
                    except ValueError:
                        continue

        # Collect icon files specifically
        if dir_name.lower() in ["icons", "resources"]:
            for pattern in icon_patterns:
                for file_path in dir_path.rglob(pattern):
                    if file_path.is_file():
                        try:
                            rel_path = file_path.relative_to(project_path_obj)
                            resources["icon_files"].append(str(rel_path))
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


def get_hidden_imports(package: Optional[str] = None) -> List[str]:
    """Get hidden imports for packaging.

    Parameters
    ----------
    package : str, optional
        Package name to get hidden imports for. If None, returns all hidden imports.

    Returns
    -------
    List[str]
        List of hidden imports
    """
    # Known hidden imports for common packages
    all_hidden_imports = {
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

    if package is None:
        # Return all hidden imports as a flat list
        all_imports = []
        for imports in all_hidden_imports.values():
            all_imports.extend(imports)
        return all_imports
    else:
        return all_hidden_imports.get(package, [])


# Alias for backward compatibility
detect_hidden_imports = get_hidden_imports


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
    ]
