"""
Release management utilities for the APGI system.

This module provides tools for managing releases, versioning, and deployment.
"""

import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class ReleaseError(Exception):
    """Custom exception for release errors."""

    pass


class ReleaseManager:
    """Manage releases for the APGI system."""

    def __init__(self, project_root: Optional[str] = None) -> None:
        """Initialize release manager.

        Parameters
        ----------
        project_root : str, optional
            Project root directory, by default None
        """
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.version_file = self.project_root / "apgi_simulation" / "__init__.py"
        self.changelog_file = self.project_root / "CHANGELOG.md"
        self.pyproject_file = self.project_root / "pyproject.toml"
        self.build_dir = self.project_root / "build"
        self.dist_dir = self.project_root / "dist"
        self.dry_run = True  # Always dry run for safety

    def get_current_version(self) -> str:
        """Get current version.

        Returns
        -------
        str
            Current version
        """
        if self.version_file.exists():
            return self.version_file.read_text().strip()

        # Try to get from pyproject.toml
        pyproject_file = self.project_root / "pyproject.toml"
        if pyproject_file.exists():
            try:
                # Try tomllib first (Python 3.11+)
                try:
                    import tomllib

                    with open(pyproject_file, "rb") as f:
                        config = tomllib.load(f)
                except ImportError:
                    # Fall back to tomli
                    try:
                        import tomli  # type: ignore[import-not-found]

                        with open(pyproject_file, "rb") as f:
                            config = tomli.load(f)
                    except ImportError:
                        # Fall back to toml with type ignore
                        import toml  # type: ignore

                        config = toml.load(str(pyproject_file))
                return config.get("project", {}).get("version", "0.1.0")
            except ImportError:
                pass

        return "0.1.0"

    def validate_version(self, version: str) -> bool:
        """Validate version string format.

        Parameters
        ----------
        version : str
            Version string to validate

        Returns
        -------
        bool
            True if valid
        """
        import re

        pattern = r"^\d+\.\d+\.\d+(-[a-zA-Z0-9]+)?$"
        return bool(re.match(pattern, version))

    def set_version(self, version: str) -> None:
        """Set current version.

        Parameters
        ----------
        version : str
            New version
        """
        self.version_file.write_text(f'__version__ = "{version}"\n')

    def bump_version(self, version: str) -> None:
        """Bump version in version files.

        Parameters
        ----------
        version : str
            New version string
        """
        if not self.validate_version(version):
            raise ReleaseError(f"Invalid version format: {version}")

        if not self.dry_run:
            # Update __init__.py
            if self.version_file.exists():
                content = self.version_file.read_text()
                import re

                content = re.sub(
                    r'__version__\s*=\s*["\'][^"\']*["\']', f'__version__ = "{version}"', content
                )
                self.version_file.write_text(content)

            # Update pyproject.toml
            if self.pyproject_file.exists():
                try:
                    # Try to update pyproject.toml
                    import tomllib

                    with open(self.pyproject_file, "rb") as f:
                        config = tomllib.load(f)
                    if "project" in config and "version" in config["project"]:
                        config["project"]["version"] = version
                        try:
                            import tomli_w  # type: ignore[import-not-found]

                            with open(self.pyproject_file, "wb") as f:
                                tomli_w.dump(config, f)
                        except ImportError:
                            pass  # Skip if tomli_w not available
                except ImportError:
                    pass  # Skip if tomllib not available

    def increment_version(self, bump_type: str = "patch") -> str:
        """Increment version.

        Parameters
        ----------
        bump_type : str, optional
            Type of bump (major, minor, patch), by default "patch"

        Returns
        -------
        str
            New version
        """
        current = self.get_current_version()
        parts = current.split(".")

        if len(parts) != 3:
            raise ReleaseError(f"Invalid version format: {current}")

        major, minor, patch = map(int, parts)

        if bump_type == "major":
            major += 1
            minor = 0
            patch = 0
        elif bump_type == "minor":
            minor += 1
            patch = 0
        elif bump_type == "patch":
            patch += 1
        else:
            raise ReleaseError(f"Invalid bump type: {bump_type}")

        new_version = f"{major}.{minor}.{patch}"
        self.set_version(new_version)
        return new_version

    def categorize_commits(self, commits: List[str]) -> Dict[str, List[str]]:
        """Categorize commits by type.

        Parameters
        ----------
        commits : List[str]
            List of commit messages

        Returns
        -------
        Dict[str, List[str]]
            Categorized commits
        """
        categories: Dict[str, List[str]] = {
            "Features": [],
            "Bug Fixes": [],
            "Documentation": [],
            "Performance": [],
            "Refactoring": [],
            "Tests": [],
            "Build": [],
            "Other": [],
        }

        import re

        for commit in commits:
            commit_lower = commit.lower()
            if re.search(r"\bfeat\b|\bfeature\b|\badd\b|\bnew\b", commit_lower):
                categories["Features"].append(commit)
            elif re.search(r"\bfix\b|\bbug\b|\bpatch\b", commit_lower):
                categories["Bug Fixes"].append(commit)
            elif re.search(r"\bdocs?\b|\bdocumentation\b|\breadme\b", commit_lower):
                categories["Documentation"].append(commit)
            elif re.search(r"\bperf\b|\bperformance\b|\boptimize\b|\bspeed\b", commit_lower):
                categories["Performance"].append(commit)
            elif re.search(r"\brefactor\b|\bclean\b|\bsimplify\b", commit_lower):
                categories["Refactoring"].append(commit)
            elif re.search(r"\btest\b|\btesting\b|\bspec\b", commit_lower):
                categories["Tests"].append(commit)
            elif re.search(r"\bbuild\b|\bbuilds\b|\bci\b|\bcd\b|\bdeploy\b", commit_lower):
                categories["Build"].append(commit)
            else:
                categories["Other"].append(commit)

        return categories

    def create_git_tag(self, version: str) -> bool:
        """Create git tag for version.

        Parameters
        ----------
        version : str
            Version to tag

        Returns
        -------
        bool
            True if tag created successfully
        """
        try:
            # Create tag
            subprocess.run(
                ["git", "tag", "-a", f"v{version}", "-m", f"Release v{version}"],
                check=True,
                cwd=self.project_root,
            )

            # Push tag
            subprocess.run(
                ["git", "push", "origin", f"v{version}"], check=True, cwd=self.project_root
            )

            return True
        except subprocess.CalledProcessError as e:
            raise ReleaseError(f"Failed to create git tag: {e}")

    def build_release(self) -> Dict[str, bool]:
        """Build release packages.

        Returns
        -------
        Dict[str, bool]
            Build results
        """
        results = {}

        try:
            # Clean previous builds
            subprocess.run(["rm", "-rf", "build", "dist"], cwd=self.project_root)

            # Build source distribution
            subprocess.run(["python", "-m", "build", "--sdist"], check=True, cwd=self.project_root)
            results["sdist"] = True

            # Build wheel
            subprocess.run(["python", "-m", "build", "--wheel"], check=True, cwd=self.project_root)
            results["wheel"] = True

        except subprocess.CalledProcessError as e:
            raise ReleaseError(f"Build failed: {e}")

        return results

    def calculate_checksum(self, file_path: Path, algorithm: str = "sha256") -> str:
        """Calculate checksum for a file.

        Parameters
        ----------
        file_path : Path
            Path to file
        algorithm : str, optional
            Hash algorithm, by default "sha256"

        Returns
        -------
        str
            Hexadecimal checksum
        """
        import hashlib

        hash_func = getattr(hashlib, algorithm)()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_func.update(chunk)
        return hash_func.hexdigest()

    def generate_checksums(self, directories: List[Path]) -> Dict[str, Dict[str, Any]]:
        """Generate checksums for files in directories.

        Parameters
        ----------
        directories : List[Path]
            List of directories to scan

        Returns
        -------
        Dict[str, Dict[str, Any]]
            Checksum data
        """
        checksums = {}

        for directory in directories:
            if directory.exists():
                for file_path in directory.rglob("*"):
                    if file_path.is_file():
                        relative_path = file_path.relative_to(self.dist_dir)
                        checksums[str(relative_path)] = {
                            "sha256": self.calculate_checksum(file_path),
                            "size": file_path.stat().st_size,
                        }

        return checksums

    def save_checksums(self, checksums: Dict[str, Dict[str, Any]], version: str) -> None:
        """Save checksums to files.

        Parameters
        ----------
        checksums : Dict[str, Dict[str, Any]]
            Checksum data
        version : str
            Version string
        """
        if not self.dry_run:
            # Save JSON
            import json

            json_file = self.dist_dir / f"checksums-{version}.json"
            with open(json_file, "w") as f:
                json.dump(checksums, f, indent=2)

            # Save text file
            txt_file = self.dist_dir / f"checksums-{version}.txt"
            with open(txt_file, "w") as f:
                f.write(f"Checksums for version {version}\n")
                f.write("=" * 40 + "\n\n")
                for file_path, data in checksums.items():
                    f.write(f"File: {file_path}\n")
                    f.write(f"SHA256: {data['sha256']}\n")
                    f.write(f"Size: {data['size']} bytes\n\n")

    def generate_changelog_entry(self, version: str, changes: List[str]) -> str:
        """Generate changelog entry.

        Parameters
        ----------
        version : str
            Version
        changes : List[str]
            List of changes

        Returns
        -------
        str
            Changelog entry
        """
        date = datetime.now().strftime("%Y-%m-%d")
        entry = f"## [{version}] - {date}\n\n"

        for change in changes:
            entry += f"- {change}\n"

        entry += "\n"
        return entry

    def update_changelog(self, version: str, changes: List[str]) -> None:
        """Update changelog with new version.

        Parameters
        ----------
        version : str
            Version
        changes : List[str]
            List of changes
        """
        entry = self.generate_changelog_entry(version, changes)

        if self.changelog_file.exists():
            current_content = self.changelog_file.read_text()
            new_content = entry + current_content
        else:
            new_content = entry

        self.changelog_file.write_text(new_content)

    def validate_environment(self) -> None:
        """Validate release environment.

        Raises
        ------
        ReleaseError
            If environment is not valid for release
        """
        # Check for git repository
        git_dir = self.project_root / ".git"
        if not git_dir.exists():
            raise ReleaseError("Not a git repository")

        # Check for version file
        if not self.version_file.exists():
            raise ReleaseError("Version file not found")

        # Check git status if not in dry run
        if not self.dry_run:
            try:
                result = subprocess.run(
                    ["git", "status", "--porcelain"],
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                    check=True,
                )
                if result.stdout.strip():
                    raise ReleaseError("Working directory has uncommitted changes")
            except subprocess.CalledProcessError:
                raise ReleaseError("Failed to check git status")

    def release(
        self,
        version: Optional[str] = None,
        changes: Optional[List[str]] = None,
        bump_type: str = "patch",
        create_tag: bool = True,
        build: bool = True,
    ) -> Dict[str, Any]:
        """Perform complete release process.

        Parameters
        ----------
        version : str, optional
            Version to release, by default None (auto-increment)
        changes : List[str], optional
            List of changes for changelog, by default None
        bump_type : str, optional
            Type of version bump, by default "patch"
        create_tag : bool, optional
            Whether to create git tag, by default True
        build : bool, optional
            Whether to build packages, by default True

        Returns
        -------
        Dict[str, Any]
            Release results
        """
        results: Dict[str, Any] = {"version": version, "success": False, "steps": {}}

        try:
            # Determine version
            if version:
                self.set_version(version)
            else:
                version = self.increment_version(bump_type)

            results["version"] = version
            results["steps"]["version_set"] = True

            # Update changelog
            if changes:
                self.update_changelog(version, changes)
                results["steps"]["changelog_updated"] = True

            # Create git tag
            if create_tag:
                self.create_git_tag(version)
                results["steps"]["git_tag_created"] = True

            # Build packages
            if build:
                build_results = self.build_release()
                results["steps"]["build"] = build_results

            results["success"] = True

        except Exception as e:
            results["error"] = str(e)
            raise ReleaseError(f"Release failed: {e}")

        return results

    def build_platform(self, platform: str) -> Optional[Path]:
        """Build for specific platform.

        Parameters
        ----------
        platform : str
            Platform to build for

        Returns
        -------
        Optional[Path]
            Path to built executable, None if skipped or failed
        """
        if self.dry_run:
            return None

        # Check if we're on the target platform
        import sys

        current_platform = sys.platform

        platform_map = {"windows": "win32", "macos": "darwin", "linux": "linux"}

        if platform_map.get(platform) != current_platform:
            return None  # Skip cross-platform builds

        # Look for build script
        build_script = self.build_dir / f"build_{platform}.py"
        if not build_script.exists():
            return None

        try:
            # Run build script
            subprocess.run([sys.executable, str(build_script)], cwd=self.project_root, check=True)

            # Assume executable is in dist directory
            return self.dist_dir / platform

        except subprocess.CalledProcessError:
            return None
