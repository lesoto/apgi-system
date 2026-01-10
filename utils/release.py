"""
Release management utilities for the APGI system.

This module provides tools for managing releases, versioning, and deployment.
"""

import os
import subprocess
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime


class ReleaseError(Exception):
    """Custom exception for release errors."""
    pass


class ReleaseManager:
    """Manage releases for the APGI system."""
    
    def __init__(self, project_root: str = None):
        """Initialize release manager.
        
        Parameters
        ----------
        project_root : str, optional
            Project root directory, by default None
        """
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.version_file = self.project_root / "VERSION"
        self.changelog_file = self.project_root / "CHANGELOG.md"
        
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
                import toml
                config = toml.load(pyproject_file)
                return config.get("project", {}).get("version", "0.1.0")
            except ImportError:
                pass
        
        return "0.1.0"
    
    def set_version(self, version: str) -> None:
        """Set current version.
        
        Parameters
        ----------
        version : str
            New version
        """
        self.version_file.write_text(version + "\n")
    
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
                cwd=self.project_root
            )
            
            # Push tag
            subprocess.run(
                ["git", "push", "origin", f"v{version}"],
                check=True,
                cwd=self.project_root
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
            subprocess.run(
                ["python", "-m", "build", "--sdist"],
                check=True,
                cwd=self.project_root
            )
            results["sdist"] = True
            
            # Build wheel
            subprocess.run(
                ["python", "-m", "build", "--wheel"],
                check=True,
                cwd=self.project_root
            )
            results["wheel"] = True
            
        except subprocess.CalledProcessError as e:
            raise ReleaseError(f"Build failed: {e}")
        
        return results
    
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
    
    def release(self, version: str = None, changes: List[str] = None, 
                bump_type: str = "patch", create_tag: bool = True, 
                build: bool = True) -> Dict[str, Any]:
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
        results = {
            "version": version,
            "success": False,
            "steps": {}
        }
        
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
