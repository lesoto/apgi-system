# Implementation Plan

- [x] 1. Set up project structure and platform abstraction layer
  - Create `resources/` directory with subdirectories for icons, images, data
  - Create `build/` directory for build scripts and configurations
  - Create `apgi_system/platform_utils.py` module with cross-platform utilities
  - Create `requirements-build.txt` with build-time dependencies
  - _Requirements: 3.1, 3.4, 4.1_

- [x] 1.1 Implement platform detection and resource path utilities
  - Write `get_platform()` function to detect Windows/macOS/Linux
  - Write `is_bundled()` function to detect if running as executable
  - Write `get_resource_path()` function for cross-platform resource loading
  - Write `get_config_dir()` and `get_data_dir()` for user-writable locations
  - _Requirements: 3.1, 3.4, 4.2_

- [x] 1.2 Write property test for platform detection
  - **Property 2: Platform detection accuracy**
  - **Validates: Requirements 3.4**

- [x] 1.3 Write property test for resource path resolution
  - **Property 1: Resource path resolution consistency**
  - **Validates: Requirements 3.4, 4.2**

- [x] 1.4 Write property test for cross-platform path compatibility
  - **Property 6: Cross-platform path compatibility**
  - **Validates: Requirements 3.1**

- [x] 2. Audit and update application code for cross-platform compatibility
  - Search for hardcoded file paths and replace with `Path` objects
  - Replace all resource file references with `get_resource_path()` calls
  - Update `apgi_gui.py` to use platform utilities for config loading
  - Review and update any platform-specific imports with conditional logic
  - Test that application runs correctly with new path handling
  - _Requirements: 3.1, 3.2, 3.3, 4.2_

- [x] 2.1 Write unit tests for updated path handling
  - Test config file loading with new paths
  - Test resource file access in GUI
  - Test data export with platform-appropriate directories
  - _Requirements: 3.1, 4.2_

- [x] 3. Create application icons for both platforms
  - Design or obtain source icon image (PNG, 1024x1024 recommended)
  - Convert to Windows .ico format with multiple resolutions (256, 128, 64, 48, 32, 16)
  - Convert to macOS .icns format with multiple resolutions
  - Place icons in `resources/icons/` directory
  - _Requirements: 7.1, 7.2, 7.3_

- [x] 4. Implement Windows build system
  - Create `build/build_common.py` with shared build utilities
  - Implement dependency analysis function
  - Implement resource collection function
  - Implement version extraction function
  - _Requirements: 5.1, 8.1, 8.2_

- [x] 4.1 Create PyInstaller configuration
  - Generate `build/pyinstaller.spec` file
  - Configure entry point to `apgi_gui.py`
  - Add hidden imports for scipy, matplotlib, tkinter dependencies
  - Configure data files to include resources/ and config/
  - Set icon path and console options
  - Add exclusions for test files and unnecessary packages
  - _Requirements: 5.2, 5.3, 5.5, 12.1, 12.2, 12.4_

- [ ] 4.2 Create Windows build script











  - Create `build/build_windows.py` with Windows-specific build logic
  - Add virtual environment creation
  - Add dependency installation
  - Add PyInstaller execution with spec file
  - Add post-build validation
  - Add error handling with clear messages
  - _Requirements: 5.1, 5.4, 8.3, 8.4, 8.5_

- [x] 4.3 Write property test for build reproducibility
  - **Property 3: Build reproducibility**
  - **Validates: Requirements 8.2, 8.4**

- [x] 4.4 Write property test for dependency completeness
  - **Property 4: Dependency completeness**
  - **Validates: Requirements 1.3, 2.3, 5.2, 6.2_

- [x] 5. Test Windows executable
  - Build Windows executable on Windows machine
  - Test executable launches without errors
  - Test all GUI controls and menu items
  - Test file operations (save/load configuration, export data)
  - Test experimental tasks execution
  - Verify icon displays correctly
  - Test on clean Windows VM without Python installed
  - _Requirements: 1.1, 1.2, 1.3, 9.1, 9.2, 9.3, 9.4_

- [x] 5.1 Write property test for executable launch success
  - **Property 7: Executable launch success**
  - **Validates: Requirements 1.2, 2.2, 9.1**

- [x] 5.2 Write property test for GUI functionality preservation
  - **Property 8: GUI functionality preservation**
  - **Validates: Requirements 9.2**

- [x] 5.3 Write property test for file I/O correctness
  - **Property 9: File I/O correctness**
  - **Validates: Requirements 9.3**

- [x] 6. Implement macOS build system




  - Create `build/build_macos.py` with macOS-specific build logic
  - Reuse common utilities from `build_common.py`
  - Implement .app bundle structure creation
  - Implement Info.plist generation
  - _Requirements: 6.1, 8.1, 8.2_


- [x] 6.1 Create py2app configuration

  - Create `build/setup_py2app.py` setup script
  - Configure entry point to `apgi_gui.py`
  - Add packages list from requirements.txt
  - Configure resources to include config/ and data files
  - Set Info.plist values (CFBundleName, CFBundleVersion, CFBundleIdentifier)
  - Set icon path
  - _Requirements: 6.2, 6.3, 6.5_

- [x] 6.2 Implement macOS build script execution


  - Add virtual environment creation
  - Add dependency installation
  - Add py2app execution
  - Add .app bundle validation
  - Add error handling with clear messages
  - _Requirements: 6.1, 6.4, 8.3, 8.4, 8.5_

- [x] 6.3 Write property test for resource bundling completeness


  - **Property 5: Resource bundling completeness**
  - **Validates: Requirements 4.1, 4.3, 7.5**


- [x] 7. Test macOS application bundle





  - Build macOS .app on macOS machine
  - Test .app bundle opens without errors
  - Test all GUI controls and menu items
  - Test file operations (save/load configuration, export data)
  - Test experimental tasks execution
  - Verify icon displays in Dock
  - Test on clean macOS without Python installed
  - _Requirements: 2.1, 2.2, 2.3, 9.1, 9.2, 9.3, 9.4_






- [ ] 7.1 Write property test for configuration persistence
  - **Property 10: Configuration persistence**
  - **Validates: Requirements 4.4**


- [x] 8. Create Windows installer with Inno Setup




  - Create `build/installer_utils.py` with utility functions
  - Create `build/installer_windows.iss` Inno Setup script
  - Configure application name, version, publisher
  - Set installation directory and Start Menu entries
  - Add desktop shortcut option
  - Configure uninstaller
  - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5_

- [x] 8.1 Write unit tests for installer script generation
  - Test version string extraction
  - Test path configuration

  - Test registry entry generation
  - _Requirements: 13.1, 13.2_


- [x] 9. Create macOS disk image (.dmg)



  - Install create-dmg or use hdiutil
  - Create `build/create_dmg.sh` script
  - Configure DMG with custom background image
  - Add Applications folder symlink

  - Set window size and icon positions
  - Build .dmg file
  - Test .dmg on clean macOS
  - _Requirements: 14.1, 14.2, 14.3, 14.4_

- [x] 9.1 Write unit tests for DMG creation script

  - Test DMG structure validation
  - Test symlink creation
  - Test file permissions
  - _Requirements: 14.1, 14.2_

- [x] 10. Optimize executable file sizes
  - Add module exclusions to build configurations (pytest, hypothesis, sphinx, etc.)
  - Configure PyInstaller to exclude unused packages
  - Test that excluded modules don't break functionality
  - Measure and document file sizes before and after optimization
  - Consider UPX compression for Windows (test thoroughly)
  - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5_

- [x] 10.1 Write unit tests for dependency analysis
  - Test module exclusion logic
  - Test hidden import detection
  - Test resource file discovery
  - _Requirements: 12.1, 12.2_

- [x] 11. Implement error handling improvements
  - Add try-catch blocks around resource loading
  - Implement graceful degradation for missing resources
  - Add user-friendly error dialogs with actionable messages
  - Implement logging for debugging bundled executables
  - Add fallback behavior for platform-specific features
  - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5_

- [x] 11.1 Write unit tests for error handling
  - Test missing resource handling
  - Test invalid configuration handling
  - Test permission denied scenarios
  - Test missing library detection
  - _Requirements: 11.1, 11.2, 11.3, 11.4_

- [x] 12. Create comprehensive build documentation
  - Create `build/README_BUILD.md` with step-by-step instructions
  - Document prerequisites for Windows builds
  - Document prerequisites for macOS builds
  - Document build script usage and options
  - Document troubleshooting for common issues
  - Document code signing process for both platforms
  - Add examples for different build configurations
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

- [x] 13. Create distribution documentation





  - Create `README_DISTRIBUTION.md` for end users
  - Document Windows installation process
  - Document macOS installation process
  - Document system requirements
  - Add troubleshooting section for common user issues



  - Add screenshots of installation process



  - _Requirements: 10.1, 10.4_

- [x] 14. Final integration testing




  - Build executables for both platforms
  - Run complete manual testing checklist (from design doc)
  - Test cross-platform configuration file compatibility
  - Test exported data file compatibility
  - Verify all experimental tasks work in bundled executables
  - Test on multiple Windows versions (10, 11)
  - Test on multiple macOS versions (12+, Intel and Apple Silicon)
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

- [x] 14.1 Write integration tests for build process




  - Test end-to-end Windows build
  - Test end-to-end macOS build
  - Test executable functionality after build
  - _Requirements: 9.1, 9.2, 9.3_


- [x] 15. Create release automation script




  - Create `build/release.py` script to automate full release process
  - Implement version bumping

  - Implement changelog generation
  - Implement building for both platforms
  - Implement creating distribution packages
  - Implement generating checksums
  - Add dry-run mode for testing
  - _Requirements: 8.1, 8.2, 8.4_

