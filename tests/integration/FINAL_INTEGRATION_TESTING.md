# Final Integration Testing

This document describes the automated integration tests for the cross-platform executable and provides guidance for manual testing that should be performed before release.

## Automated Tests

The automated integration tests in `test_final_integration.py` verify the following:

### 1. Cross-Platform Configuration Compatibility (Requirements 9.3, 9.4, 9.5)

✅ **Configuration YAML Round Trip**: Verifies that configuration can be saved and loaded without data loss
✅ **Cross-Platform Paths**: Ensures configuration with paths works across Windows, macOS, and Linux
✅ **Special Characters**: Tests that configuration handles special characters and unicode correctly
✅ **Default Values**: Verifies that missing configuration values can be filled with defaults

### 2. Exported Data Compatibility (Requirements 9.3, 9.5)

✅ **JSON Export Round Trip**: Verifies JSON export preserves data integrity
✅ **CSV Export Compatibility**: Tests CSV export works across platforms
✅ **NumPy Export Compatibility**: Ensures numpy array export works cross-platform
✅ **Export with Metadata**: Tests that exports include platform metadata for compatibility

### 3. Experimental Tasks Execution (Requirements 9.2, 9.4)

✅ **Iowa Gambling Task**: Import and execution tests
✅ **Masking Paradigm**: Import and execution tests
✅ **Attentional Blink**: Import and execution tests
✅ **All Tasks Available**: Verifies all experimental tasks can be imported

### 4. Platform-Specific Features (Requirements 9.4)

✅ **Platform Detection**: Verifies correct platform identification
✅ **Platform Utilities**: Tests platform utility functions
✅ **File Dialog Availability**: Ensures GUI file dialogs are available
✅ **User Data Directory Access**: Tests access to platform-appropriate data directories

### 5. Resource Bundling (Requirements 9.3)

✅ **Config Files Accessible**: Verifies configuration files can be read
✅ **Icon Files Accessible**: Tests that icon files are accessible
✅ **Resource Path Resolution**: Ensures resource paths resolve correctly in bundled environment

### 6. Error Handling (Requirements 9.3)

✅ **Missing Resource Handling**: Tests graceful handling of missing resources
✅ **Invalid Config Handling**: Verifies invalid configuration is handled properly
✅ **Permission Denied Handling**: Tests handling of permission errors

## Test Results

All 25 automated integration tests pass successfully:

```
tests/integration/test_final_integration.py::TestCrossPlatformConfigCompatibility::test_config_yaml_round_trip PASSED
tests/integration/test_final_integration.py::TestCrossPlatformConfigCompatibility::test_config_cross_platform_paths PASSED
tests/integration/test_final_integration.py::TestCrossPlatformConfigCompatibility::test_config_with_special_characters PASSED
tests/integration/test_final_integration.py::TestCrossPlatformConfigCompatibility::test_config_default_values PASSED
tests/integration/test_final_integration.py::TestExportedDataCompatibility::test_json_export_round_trip PASSED
tests/integration/test_final_integration.py::TestExportedDataCompatibility::test_csv_export_compatibility PASSED
tests/integration/test_final_integration.py::TestExportedDataCompatibility::test_numpy_export_compatibility PASSED
tests/integration/test_final_integration.py::TestExportedDataCompatibility::test_export_with_metadata PASSED
tests/integration/test_final_integration.py::TestExperimentalTasksExecution::test_iowa_gambling_task_import PASSED
tests/integration/test_final_integration.py::TestExperimentalTasksExecution::test_iowa_gambling_task_execution PASSED
tests/integration/test_final_integration.py::TestExperimentalTasksExecution::test_masking_paradigm_import PASSED
tests/integration/test_final_integration.py::TestExperimentalTasksExecution::test_masking_paradigm_execution PASSED
tests/integration/test_final_integration.py::TestExperimentalTasksExecution::test_attentional_blink_import PASSED
tests/integration/test_final_integration.py::TestExperimentalTasksExecution::test_attentional_blink_execution PASSED
tests/integration/test_final_integration.py::TestExperimentalTasksExecution::test_all_experimental_tasks_available PASSED
tests/integration/test_final_integration.py::TestPlatformSpecificFeatures::test_platform_detection PASSED
tests/integration/test_final_integration.py::TestPlatformSpecificFeatures::test_platform_utils_available PASSED
tests/integration/test_final_integration.py::TestPlatformSpecificFeatures::test_file_dialog_availability PASSED
tests/integration/test_final_integration.py::TestPlatformSpecificFeatures::test_user_data_directory_access PASSED
tests/integration/test_final_integration.py::TestResourceBundling::test_config_files_accessible PASSED
tests/integration/test_final_integration.py::TestResourceBundling::test_icon_files_accessible PASSED
tests/integration/test_final_integration.py::TestResourceBundling::test_resource_path_resolution_in_bundled_env PASSED
tests/integration/test_final_integration.py::TestErrorHandlingInBundledEnv::test_missing_resource_handling PASSED
tests/integration/test_final_integration.py::TestErrorHandlingInBundledEnv::test_invalid_config_handling PASSED
tests/integration/test_final_integration.py::TestErrorHandlingInBundledEnv::test_permission_denied_handling PASSED
```

## Manual Testing Checklist

While automated tests verify core functionality, the following manual tests should be performed on actual built executables before release:

### Windows Testing (Requirements 9.1, 9.2, 9.3, 9.4)

**Windows 10:**
- [ ] Executable launches from double-click
- [ ] GUI displays correctly
- [ ] All menu items work
- [ ] File dialogs open correctly
- [ ] Configuration saves and loads
- [ ] Data export works
- [ ] Application icon displays
- [ ] No console window appears (unless debug build)
- [ ] All experimental tasks execute successfully
- [ ] Uninstaller removes all files (if using installer)

**Windows 11:**
- [ ] Executable launches from double-click
- [ ] GUI displays correctly
- [ ] All menu items work
- [ ] File dialogs open correctly
- [ ] Configuration saves and loads
- [ ] Data export works
- [ ] Application icon displays
- [ ] No console window appears (unless debug build)
- [ ] All experimental tasks execute successfully
- [ ] Uninstaller removes all files (if using installer)

### macOS Testing (Requirements 9.1, 9.2, 9.3, 9.4)

**macOS 12+ (Intel):**
- [ ] .app bundle opens from Finder
- [ ] GUI displays correctly
- [ ] All menu items work
- [ ] File dialogs open correctly
- [ ] Configuration saves and loads
- [ ] Data export works
- [ ] Application icon displays in Dock
- [ ] Gatekeeper allows execution
- [ ] All experimental tasks execute successfully
- [ ] Application moves to Trash cleanly

**macOS 12+ (Apple Silicon):**
- [ ] .app bundle opens from Finder
- [ ] GUI displays correctly
- [ ] All menu items work
- [ ] File dialogs open correctly
- [ ] Configuration saves and loads
- [ ] Data export works
- [ ] Application icon displays in Dock
- [ ] Gatekeeper allows execution
- [ ] All experimental tasks execute successfully
- [ ] Application moves to Trash cleanly

### Cross-Platform Compatibility Testing (Requirements 9.5)

- [ ] Configuration file created on Windows loads correctly on macOS
- [ ] Configuration file created on macOS loads correctly on Windows
- [ ] Data exported on Windows can be imported on macOS
- [ ] Data exported on macOS can be imported on Windows
- [ ] Keyboard shortcuts work correctly on both platforms
- [ ] Window sizing and positioning work on both platforms

### Performance Testing

- [ ] Application startup time is acceptable (< 5 seconds)
- [ ] GUI remains responsive during long-running tasks
- [ ] Memory usage is reasonable (< 500 MB for typical usage)
- [ ] No memory leaks during extended use

### Error Handling Testing

- [ ] Missing configuration file is handled gracefully
- [ ] Invalid configuration file shows clear error message
- [ ] Missing resource files don't crash the application
- [ ] Permission denied errors show actionable messages
- [ ] Network errors (if applicable) are handled gracefully

## Running Automated Tests

To run the automated integration tests:

```bash
# Run all final integration tests
python -m pytest tests/integration/test_final_integration.py -v

# Run specific test class
python -m pytest tests/integration/test_final_integration.py::TestCrossPlatformConfigCompatibility -v

# Run with coverage
python -m pytest tests/integration/test_final_integration.py --cov=apgi_system --cov-report=html
```

## Building Executables for Testing

### Windows

```bash
# Build Windows executable
python build/build_windows.py --clean --onefile --no-console

# Output will be in dist/windows/
```

### macOS

```bash
# Build macOS application
python build/build_macos.py --clean --create-dmg

# Output will be in dist/macos/
```

## Test Environment Requirements

### For Automated Tests

- Python 3.9+
- All dependencies from requirements.txt
- pytest and pytest-cov

### For Manual Tests

- Clean Windows 10/11 VM without Python installed
- Clean macOS 12+ VM without Python installed
- Both Intel and Apple Silicon Macs (if available)

## Known Issues

None at this time. All automated tests pass successfully.

## Next Steps

1. ✅ Complete automated integration tests
2. ⏳ Build executables for both platforms
3. ⏳ Perform manual testing on Windows 10/11
4. ⏳ Perform manual testing on macOS 12+ (Intel and Apple Silicon)
5. ⏳ Verify cross-platform data compatibility
6. ⏳ Address any issues found during manual testing
7. ⏳ Prepare for release

## Contact

For questions or issues with testing, please contact the development team.
