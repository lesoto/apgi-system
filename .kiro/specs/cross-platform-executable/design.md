# Design Document

## Overview

This design document outlines the architecture and implementation strategy for porting the APGI System Python/Tkinter application to Windows and macOS as standalone executables. The solution uses PyInstaller for Windows and py2app for macOS, with a unified build system that handles platform-specific requirements automatically.

The design emphasizes:
- **Cross-platform compatibility** through platform-agnostic code patterns
- **Automated build processes** with minimal manual intervention
- **Professional distribution** with proper icons, installers, and signing
- **Maintainability** through clear separation of build configuration from application code

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    APGI Application                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   GUI Layer  │  │  Core System │  │  Resources   │      │
│  │  (Tkinter)   │  │   (APGI)     │  │ (Config/Data)│      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              Platform Abstraction Layer                      │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Path Resolution │ Resource Loading │ Platform Utils │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
              ┌─────────────┴─────────────┐
              ▼                           ▼
    ┌──────────────────┐        ┌──────────────────┐
    │  Windows Build   │        │   macOS Build    │
    │  (PyInstaller)   │        │    (py2app)      │
    └──────────────────┘        └──────────────────┘
              │                           │
              ▼                           ▼
    ┌──────────────────┐        ┌──────────────────┐
    │   .exe + DLLs    │        │   .app Bundle    │
    │   + Installer    │        │   + .dmg Image   │
    └──────────────────┘        └──────────────────┘
```

### Directory Structure

```
apgi_system/
├── apgi_gui.py                 # Main entry point
├── apgi_system/                # Core application code
├── config/                     # Configuration files
│   └── default.yaml
├── resources/                  # NEW: Resource files
│   ├── icons/
│   │   ├── apgi.ico           # Windows icon
│   │   ├── apgi.icns          # macOS icon
│   │   └── apgi.png           # Source icon
│   ├── images/                # Application images
│   └── data/                  # Data files
├── build/                      # NEW: Build scripts and configs
│   ├── build_windows.py       # Windows build script
│   ├── build_macos.py         # macOS build script
│   ├── build_common.py        # Shared build utilities
│   ├── pyinstaller.spec       # PyInstaller configuration
│   ├── setup_py2app.py        # py2app setup script
│   └── README_BUILD.md        # Build documentation
├── dist/                       # Build output (gitignored)
│   ├── windows/
│   └── macos/
├── requirements.txt            # Runtime dependencies
├── requirements-build.txt      # NEW: Build-time dependencies
└── README_DISTRIBUTION.md      # NEW: Distribution guide
```

## Components and Interfaces

### 1. Platform Abstraction Module

**Purpose:** Provide cross-platform utilities for path resolution and resource loading.

**Location:** `apgi_system/platform_utils.py`

**Interface:**
```python
def get_resource_path(relative_path: str) -> Path:
    """
    Get absolute path to resource, works for dev and bundled environments.
    
    Args:
        relative_path: Path relative to application root
        
    Returns:
        Absolute path to resource
    """

def get_config_dir() -> Path:
    """
    Get platform-appropriate configuration directory.
    
    Returns:
        Path to config directory (user-writable)
    """

def get_data_dir() -> Path:
    """
    Get platform-appropriate data directory.
    
    Returns:
        Path to data directory (user-writable)
    """

def is_bundled() -> bool:
    """
    Check if running as bundled executable.
    
    Returns:
        True if bundled, False if running from source
    """

def get_platform() -> str:
    """
    Get current platform identifier.
    
    Returns:
        'windows', 'macos', or 'linux'
    """
```

### 2. Build System

**Purpose:** Automate executable creation for each platform.

#### Windows Build Script (`build/build_windows.py`)

**Responsibilities:**
- Create virtual environment
- Install dependencies
- Generate PyInstaller spec file
- Execute PyInstaller
- Create installer with Inno Setup (optional)
- Sign executable (if credentials provided)

**Interface:**
```python
def build_windows_executable(
    clean: bool = True,
    onefile: bool = True,
    console: bool = False,
    sign: bool = False
) -> Path:
    """
    Build Windows executable.
    
    Args:
        clean: Remove previous build artifacts
        onefile: Create single-file executable
        console: Show console window
        sign: Code-sign the executable
        
    Returns:
        Path to built executable
    """
```

#### macOS Build Script (`build/build_macos.py`)

**Responsibilities:**
- Create virtual environment
- Install dependencies
- Generate py2app setup script
- Execute py2app
- Create .dmg disk image
- Sign and notarize (if credentials provided)

**Interface:**
```python
def build_macos_app(
    clean: bool = True,
    sign: bool = False,
    notarize: bool = False,
    create_dmg: bool = True
) -> Path:
    """
    Build macOS application bundle.
    
    Args:
        clean: Remove previous build artifacts
        sign: Code-sign the application
        notarize: Submit for Apple notarization
        create_dmg: Create .dmg disk image
        
    Returns:
        Path to built .app bundle or .dmg
    """
```

### 3. Resource Management

**Purpose:** Ensure all non-code files are properly bundled and accessible.

**Strategy:**
- Store all resources in `resources/` directory
- Use `get_resource_path()` for all resource access
- Declare resources in build configurations
- Support both development and bundled environments

### 4. Configuration Management

**Purpose:** Handle configuration files in both development and production.

**Strategy:**
- Bundle default configuration in `resources/config/`
- Store user configuration in platform-appropriate location
- Merge default and user configurations at runtime
- Support configuration export/import

## Data Models

### Build Configuration

```python
@dataclass
class BuildConfig:
    """Configuration for executable build."""
    
    app_name: str = "APGI System"
    version: str = "1.0.0"
    author: str = "APGI Team"
    description: str = "Allostatic Precision-Gated Ignition Framework"
    
    # Entry point
    entry_script: str = "apgi_gui.py"
    
    # Icons
    windows_icon: str = "resources/icons/apgi.ico"
    macos_icon: str = "resources/icons/apgi.icns"
    
    # Resources to bundle
    data_files: List[Tuple[str, str]] = field(default_factory=list)
    
    # Hidden imports (not auto-detected)
    hidden_imports: List[str] = field(default_factory=list)
    
    # Excluded modules
    excludes: List[str] = field(default_factory=list)
    
    # Build options
    console: bool = False
    onefile: bool = True
    
    # Signing
    sign_identity: Optional[str] = None
    entitlements: Optional[str] = None
```

### Platform Detection

```python
class Platform(Enum):
    """Supported platforms."""
    WINDOWS = "windows"
    MACOS = "macos"
    LINUX = "linux"
    UNKNOWN = "unknown"

@dataclass
class PlatformInfo:
    """Platform-specific information."""
    
    platform: Platform
    architecture: str  # 'x86_64', 'arm64', etc.
    python_version: str
    is_bundled: bool
    executable_path: Path
    resource_base: Path
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Resource path resolution consistency

*For any* resource file path, calling `get_resource_path()` should return a valid absolute path that exists in both development and bundled environments.

**Validates: Requirements 3.4, 4.2**

### Property 2: Platform detection accuracy

*For any* execution environment, `get_platform()` should return the correct platform identifier that matches the actual operating system.

**Validates: Requirements 3.4**

### Property 3: Build reproducibility

*For any* given source code state and build configuration, running the build script multiple times should produce functionally equivalent executables.

**Validates: Requirements 8.2, 8.4**

### Property 4: Dependency completeness

*For any* Python import statement in the application code, the bundled executable should include the corresponding module or raise a clear error during build.

**Validates: Requirements 1.3, 2.3, 5.2, 6.2**

### Property 5: Resource bundling completeness

*For any* resource file referenced in the code, the bundled executable should include that resource or the build should fail with a clear error.

**Validates: Requirements 4.1, 4.3, 7.5**

### Property 6: Cross-platform path compatibility

*For any* file path constructed in the code, it should work correctly on both Windows and macOS without modification.

**Validates: Requirements 3.1**

### Property 7: Executable launch success

*For any* valid build output, double-clicking the executable should launch the GUI application without errors.

**Validates: Requirements 1.2, 2.2, 9.1**

### Property 8: GUI functionality preservation

*For any* GUI interaction available in the source application, the bundled executable should support the same interaction with identical behavior.

**Validates: Requirements 9.2**

### Property 9: File I/O correctness

*For any* file read or write operation, the bundled executable should perform the operation successfully in user-writable locations.

**Validates: Requirements 9.3**

### Property 10: Configuration persistence

*For any* configuration change saved by the user, reopening the application should restore that configuration.

**Validates: Requirements 4.4**

## Error Handling

### Build-Time Errors

1. **Missing Dependencies**
   - Detection: Check for required tools (PyInstaller, py2app, icon tools)
   - Handling: Display installation instructions and exit gracefully
   - Recovery: User installs missing tools and retries

2. **Import Analysis Failures**
   - Detection: PyInstaller/py2app reports missing modules
   - Handling: Add to hidden_imports list automatically or prompt user
   - Recovery: Rebuild with updated configuration

3. **Resource Collection Failures**
   - Detection: Referenced resource files not found
   - Handling: List missing resources and exit with error
   - Recovery: User adds missing resources or updates references

4. **Icon Conversion Failures**
   - Detection: Icon files missing or invalid format
   - Handling: Use default icon and log warning
   - Recovery: Continue build with default icon

5. **Signing Failures**
   - Detection: Certificate not found or invalid
   - Handling: Build unsigned executable with warning
   - Recovery: User provides valid certificate or accepts unsigned build

### Runtime Errors

1. **Resource Not Found**
   - Detection: `get_resource_path()` returns non-existent path
   - Handling: Log error, use fallback resource or graceful degradation
   - User Message: "Resource file not found: {path}. Some features may be unavailable."

2. **Configuration Load Failure**
   - Detection: Config file missing or invalid YAML
   - Handling: Use default configuration
   - User Message: "Configuration file invalid. Using defaults."

3. **Permission Denied**
   - Detection: File I/O operations fail with permission error
   - Handling: Prompt for alternative location or read-only mode
   - User Message: "Cannot write to {path}. Please choose another location."

4. **Missing Library**
   - Detection: ImportError at runtime
   - Handling: Display error dialog with troubleshooting steps
   - User Message: "Required library missing: {library}. Please reinstall the application."

5. **Platform Incompatibility**
   - Detection: Platform-specific code fails on wrong platform
   - Handling: Skip feature or use fallback implementation
   - User Message: "Feature not available on this platform."

## Testing Strategy

### Unit Tests

1. **Platform Utilities**
   - Test `get_resource_path()` with various inputs
   - Test `get_platform()` on each platform
   - Test `is_bundled()` in both environments
   - Test path construction with different separators

2. **Build Configuration**
   - Test configuration loading from files
   - Test configuration validation
   - Test default value handling

3. **Resource Management**
   - Test resource discovery
   - Test resource path resolution
   - Test missing resource handling

### Integration Tests

1. **Build Process**
   - Test complete build on Windows
   - Test complete build on macOS
   - Test clean build (remove artifacts first)
   - Test incremental build

2. **Executable Functionality**
   - Test GUI launches without errors
   - Test all menu items function correctly
   - Test file operations (save/load)
   - Test configuration persistence
   - Test resource loading

### Property-Based Tests

Property-based testing will use the `hypothesis` library (already in requirements.txt) to verify universal properties across many inputs.

**Configuration:**
- Minimum 100 iterations per property test
- Use appropriate generators for paths, strings, and platform identifiers
- Tag each test with the property it validates

**Test Organization:**
- Property tests in `tests/property/test_properties_executable.py`
- Each property gets its own test function
- Tests run as part of CI/CD pipeline

### Manual Testing Checklist

**Windows:**
- [ ] Executable launches from double-click
- [ ] GUI displays correctly
- [ ] All menu items work
- [ ] File dialogs open correctly
- [ ] Configuration saves and loads
- [ ] Data export works
- [ ] Application icon displays
- [ ] No console window appears (unless debug build)
- [ ] Uninstaller removes all files

**macOS:**
- [ ] .app bundle opens from Finder
- [ ] GUI displays correctly
- [ ] All menu items work
- [ ] File dialogs open correctly
- [ ] Configuration saves and loads
- [ ] Data export works
- [ ] Application icon displays in Dock
- [ ] Gatekeeper allows execution
- [ ] Application moves to Trash cleanly

**Cross-Platform:**
- [ ] Same configuration file works on both platforms
- [ ] Exported data files are compatible
- [ ] Keyboard shortcuts work correctly
- [ ] Window sizing and positioning work
- [ ] All experimental tasks execute successfully

## Build Process Details

### Windows Build Process

1. **Environment Setup**
   ```bash
   python -m venv build_env
   build_env\Scripts\activate
   pip install -r requirements.txt
   pip install -r requirements-build.txt
   ```

2. **Icon Preparation**
   - Convert PNG to ICO format (256x256, 128x128, 64x64, 48x48, 32x32, 16x16)
   - Place in `resources/icons/apgi.ico`

3. **PyInstaller Configuration**
   - Generate spec file with all dependencies
   - Include hidden imports: `['pkg_resources.py2_warn', 'scipy._lib.messagestream']`
   - Exclude unnecessary packages: `['pytest', 'hypothesis', 'sphinx']`
   - Bundle data files: config, resources

4. **Build Execution**
   ```bash
   pyinstaller build/pyinstaller.spec --clean --noconfirm
   ```

5. **Post-Build**
   - Test executable
   - Create installer with Inno Setup (optional)
   - Sign executable with signtool (optional)

6. **Output**
   - `dist/windows/APGI_System.exe` (single file)
   - OR `dist/windows/APGI_System/` (directory with dependencies)
   - `dist/windows/APGI_System_Setup.exe` (installer, optional)

### macOS Build Process

1. **Environment Setup**
   ```bash
   python3 -m venv build_env
   source build_env/bin/activate
   pip install -r requirements.txt
   pip install -r requirements-build.txt
   ```

2. **Icon Preparation**
   - Convert PNG to ICNS format with multiple resolutions
   - Place in `resources/icons/apgi.icns`
   - Tool: `iconutil` or `png2icns`

3. **py2app Configuration**
   - Create setup.py with py2app options
   - Include packages: all from requirements.txt
   - Include resources: config, data files
   - Set Info.plist values: CFBundleName, CFBundleVersion, etc.

4. **Build Execution**
   ```bash
   python build/setup_py2app.py py2app
   ```

5. **Post-Build**
   - Test .app bundle
   - Sign with codesign (optional)
   - Create .dmg with create-dmg or hdiutil
   - Notarize with Apple (optional)

6. **Output**
   - `dist/macos/APGI System.app` (application bundle)
   - `dist/macos/APGI_System.dmg` (disk image)

### Common Build Utilities

**Dependency Analysis:**
```python
def analyze_dependencies(entry_point: str) -> Set[str]:
    """
    Analyze Python imports to find all dependencies.
    
    Returns:
        Set of package names
    """
```

**Resource Collection:**
```python
def collect_resources(base_dir: Path) -> List[Tuple[str, str]]:
    """
    Collect all resource files for bundling.
    
    Returns:
        List of (source, destination) tuples
    """
```

**Version Management:**
```python
def get_version() -> str:
    """
    Extract version from application code or git tags.
    
    Returns:
        Version string (e.g., "1.0.0")
    """
```

## Distribution Strategy

### Windows Distribution

**Option 1: Single Executable**
- Pros: Simple, one file to download
- Cons: Larger file size, slower startup
- Use Case: Quick distribution, portable app

**Option 2: Directory Bundle**
- Pros: Faster startup, smaller individual files
- Cons: Multiple files, requires zip
- Use Case: Advanced users, network deployment

**Option 3: Installer (Recommended)**
- Pros: Professional, Start Menu integration, uninstaller
- Cons: Requires Inno Setup or similar
- Use Case: General distribution

**Recommended:** Provide both single executable and installer.

### macOS Distribution

**Option 1: .app Bundle**
- Pros: Native format, drag-to-install
- Cons: Requires zip for download
- Use Case: Direct distribution

**Option 2: .dmg Disk Image (Recommended)**
- Pros: Professional, standard Mac format, custom background
- Cons: Slightly larger file
- Use Case: General distribution

**Option 3: .pkg Installer**
- Pros: System-wide installation, pre/post scripts
- Cons: More complex, requires admin
- Use Case: Enterprise deployment

**Recommended:** Provide .dmg with drag-to-Applications interface.

### Code Signing

**Windows:**
- Requires: Authenticode certificate from trusted CA
- Tool: `signtool.exe` (Windows SDK)
- Command: `signtool sign /f cert.pfx /p password /t http://timestamp.digicert.com APGI_System.exe`
- Benefit: No SmartScreen warnings

**macOS:**
- Requires: Apple Developer account ($99/year)
- Tool: `codesign` (Xcode Command Line Tools)
- Command: `codesign --deep --force --verify --verbose --sign "Developer ID Application: Your Name" APGI\ System.app`
- Notarization: `xcrun notarytool submit APGI_System.dmg --wait`
- Benefit: Passes Gatekeeper without warnings

### File Size Optimization

**Techniques:**
1. Exclude test files and documentation
2. Use `--exclude-module` for unused packages
3. Compress with UPX (Windows only, use cautiously)
4. Strip debug symbols from libraries
5. Use `--onefile` mode for single executable

**Expected Sizes:**
- Windows .exe: 150-250 MB (with all dependencies)
- macOS .app: 180-280 MB (with frameworks)
- After compression: 50-100 MB

## Platform-Specific Considerations

### Windows

**Path Handling:**
- Use `Path` objects, not string concatenation
- Handle both forward and backslashes
- Respect Windows path length limits (260 characters)

**DLL Dependencies:**
- Bundle Visual C++ redistributables if needed
- Include any .dll files from scipy, numpy
- Test on clean Windows VM

**Registry:**
- Installer can add registry entries
- Store user preferences in `%APPDATA%\APGI System\`

**Antivirus:**
- Some AV software flags PyInstaller executables
- Code signing reduces false positives
- Submit to VirusTotal for reputation

### macOS

**Application Bundle Structure:**
```
APGI System.app/
├── Contents/
│   ├── Info.plist          # Application metadata
│   ├── MacOS/
│   │   └── APGI System     # Executable
│   ├── Resources/
│   │   ├── apgi.icns       # Icon
│   │   ├── config/         # Configuration
│   │   └── data/           # Data files
│   └── Frameworks/         # Bundled libraries
```

**Gatekeeper:**
- Unsigned apps require right-click > Open
- Signed apps open normally
- Notarized apps have no warnings

**Retina Display:**
- Ensure icon has @2x resolutions
- Test on high-DPI displays
- Tkinter handles scaling automatically

**Permissions:**
- Store user data in `~/Library/Application Support/APGI System/`
- Request permissions for file access if needed
- Respect macOS sandbox restrictions

## Dependencies

### Runtime Dependencies
(from requirements.txt - already specified)

### Build Dependencies
(new file: requirements-build.txt)

```
# Windows
pyinstaller==6.3.0
pywin32==306  # Windows only

# macOS
py2app==0.28.7  # macOS only

# Icon tools
Pillow==10.1.0  # For icon conversion

# Build utilities
setuptools>=65.0
wheel
```

### System Dependencies

**Windows:**
- Python 3.9+ (for building)
- Visual Studio Build Tools (for some packages)
- Inno Setup (optional, for installer)
- Windows SDK (optional, for signing)

**macOS:**
- Python 3.9+ (for building)
- Xcode Command Line Tools
- create-dmg (optional, for DMG creation)
- Apple Developer account (optional, for signing)

## Security Considerations

1. **Code Signing**
   - Prevents tampering
   - Establishes developer identity
   - Required for macOS notarization

2. **Dependency Verification**
   - Pin dependency versions
   - Verify package hashes
   - Use trusted package sources

3. **Resource Validation**
   - Validate configuration files before loading
   - Sanitize file paths from user input
   - Check file permissions before access

4. **Update Mechanism**
   - Consider auto-update framework
   - Verify update signatures
   - Use HTTPS for downloads

5. **User Data Protection**
   - Store sensitive data encrypted
   - Use platform keychain for credentials
   - Clear temporary files on exit

## Performance Considerations

1. **Startup Time**
   - Single-file executables are slower (extraction overhead)
   - Directory bundles start faster
   - Lazy-load heavy modules

2. **Memory Usage**
   - Bundled apps use more memory than source
   - Monitor for memory leaks in long-running sessions
   - Profile with platform tools

3. **File Size**
   - Balance between convenience and download size
   - Provide both full and minimal builds if needed
   - Use compression for distribution

## Future Enhancements

1. **Linux Support**
   - Add AppImage or Snap packaging
   - Test on major distributions
   - Handle different desktop environments

2. **Auto-Update**
   - Implement update checking
   - Download and apply updates
   - Rollback on failure

3. **Crash Reporting**
   - Integrate Sentry or similar
   - Collect anonymous crash reports
   - Improve error diagnostics

4. **Continuous Integration**
   - Automate builds on GitHub Actions
   - Build for both platforms on each release
   - Run tests on built executables

5. **Localization**
   - Support multiple languages
   - Bundle translation files
   - Detect system locale

## References

- PyInstaller Documentation: https://pyinstaller.org/
- py2app Documentation: https://py2app.readthedocs.io/
- Apple Code Signing Guide: https://developer.apple.com/documentation/security/notarizing_macos_software_before_distribution
- Windows Code Signing: https://docs.microsoft.com/en-us/windows/win32/seccrypto/cryptography-tools
