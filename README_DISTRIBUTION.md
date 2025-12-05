# APGI System - Installation Guide

Welcome to the APGI System (Allostatic Precision-Gated Ignition Framework)! This guide will help you install and run the application on your computer.

## Table of Contents

- [System Requirements](#system-requirements)
- [Windows Installation](#windows-installation)
- [macOS Installation](#macos-installation)
- [First Launch](#first-launch)
- [Troubleshooting](#troubleshooting)
- [Uninstallation](#uninstallation)
- [Getting Help](#getting-help)

---

## System Requirements

### Windows

- **Operating System:** Windows 10 or Windows 11 (64-bit)
- **RAM:** 4 GB minimum, 8 GB recommended
- **Disk Space:** 500 MB free space
- **Display:** 1280x720 minimum resolution
- **Additional:** No Python installation required

### macOS

- **Operating System:** macOS 12 (Monterey) or later
- **RAM:** 4 GB minimum, 8 GB recommended
- **Disk Space:** 500 MB free space
- **Display:** 1280x720 minimum resolution
- **Processor:** Intel or Apple Silicon (M1/M2/M3)
- **Additional:** No Python installation required

---

## Windows Installation

### Method 1: Using the Installer (Recommended)

1. **Download the Installer**
   - Download `APGI_System_Setup.exe` from the official distribution source
   - Save it to your Downloads folder

2. **Run the Installer**
   - Double-click `APGI_System_Setup.exe`
   - If Windows SmartScreen appears, click "More info" then "Run anyway"
   - The installer wizard will open

3. **Follow the Installation Wizard**
   - Click "Next" on the welcome screen
   - Review and accept the license agreement
   - Choose installation location (default: `C:\Program Files\APGI System\`)
   - Select additional tasks:
     - ✓ Create a desktop shortcut (recommended)
     - ✓ Create a Start Menu entry (recommended)
   - Click "Install" to begin installation

4. **Complete Installation**
   - Wait for the installation to complete (usually 1-2 minutes)
   - Click "Finish" to exit the installer
   - Optionally, check "Launch APGI System" to start immediately

5. **Launch the Application**
   - From Desktop: Double-click the "APGI System" icon
   - From Start Menu: Search for "APGI System" and click to launch

### Method 2: Standalone Executable

1. **Download the Executable**
   - Download `APGI_System.exe` from the official distribution source
   - Save it to a folder of your choice (e.g., `C:\APGI\`)

2. **Run the Application**
   - Double-click `APGI_System.exe` to launch
   - If Windows SmartScreen appears, click "More info" then "Run anyway"
   - The application will start immediately

3. **Create a Shortcut (Optional)**
   - Right-click `APGI_System.exe`
   - Select "Create shortcut"
   - Drag the shortcut to your Desktop or Start Menu

**Note:** The standalone executable is portable and can be run from any location, including USB drives.

---

## macOS Installation

### Using the Disk Image (.dmg)

1. **Download the Disk Image**
   - Download `APGI_System.dmg` from the official distribution source
   - Save it to your Downloads folder

2. **Open the Disk Image**
   - Double-click `APGI_System.dmg` to mount it
   - A new window will open showing the APGI System icon and an Applications folder shortcut

3. **Install the Application**
   - Drag the "APGI System" icon to the "Applications" folder shortcut
   - Wait for the copy to complete (usually a few seconds)
   - You can now eject the disk image by right-clicking it in Finder and selecting "Eject"

4. **First Launch**
   - Open Finder and go to Applications
   - Find "APGI System" in the list
   - Double-click to launch

5. **Security Prompt (First Launch Only)**
   - If you see "APGI System cannot be opened because it is from an unidentified developer":
     - Click "OK" to dismiss the dialog
     - Open System Settings (or System Preferences)
     - Go to "Privacy & Security"
     - Scroll down to find "APGI System was blocked from use"
     - Click "Open Anyway"
     - Confirm by clicking "Open" in the dialog
   - The application will now launch and won't require this step again

**Alternative Method:** Right-click (or Control-click) the application and select "Open" from the menu. This bypasses Gatekeeper for the first launch.

---

## First Launch

### Initial Setup

When you first launch APGI System, the application will:

1. **Create Configuration Directory**
   - Windows: `%APPDATA%\APGI System\`
   - macOS: `~/Library/Application Support/APGI System/`

2. **Load Default Configuration**
   - The application comes with sensible defaults
   - You can customize settings through the GUI

3. **Display Main Window**
   - The main APGI System interface will appear
   - All experimental tasks and controls will be available

### Quick Start

1. **Explore the Interface**
   - The main window shows the APGI system controls
   - Menu bar provides access to all features

2. **Run a Test Simulation**
   - Select an experimental task from the menu
   - Click "Run" to execute
   - View results in the output panel

3. **Save Your Configuration**
   - Modify parameters as needed
   - Use File → Save Configuration to preserve your settings
   - Your configuration will be loaded automatically on next launch

---

## Troubleshooting

### Windows Issues

#### Application Won't Start

**Problem:** Double-clicking the executable does nothing or shows an error.

**Solutions:**
- Ensure you're running Windows 10 or 11 (64-bit)
- Right-click the executable and select "Run as administrator"
- Check if antivirus software is blocking the application
- Try downloading the file again (it may be corrupted)
- Temporarily disable Windows Defender and try again

#### SmartScreen Warning

**Problem:** Windows SmartScreen prevents the application from running.

**Solution:**
1. Click "More info" on the SmartScreen dialog
2. Click "Run anyway" button
3. This is normal for unsigned applications and only appears once

#### Missing DLL Errors

**Problem:** Error message about missing VCRUNTIME140.dll or similar.

**Solution:**
1. Download and install Microsoft Visual C++ Redistributable
2. Get it from: https://aka.ms/vs/17/release/vc_redist.x64.exe
3. Restart your computer and try again

#### Application Crashes on Startup

**Problem:** Application starts but immediately closes or crashes.

**Solutions:**
- Check if you have sufficient RAM (4 GB minimum)
- Close other applications to free up memory
- Check Windows Event Viewer for error details
- Try running from Command Prompt to see error messages:
  ```
  cd "C:\Program Files\APGI System"
  "APGI System.exe"
  ```

#### Can't Save Configuration

**Problem:** Error when trying to save configuration or export data.

**Solutions:**
- Ensure you have write permissions to your user folder
- Try running as administrator
- Check available disk space (need at least 100 MB free)
- Manually create the config directory: `%APPDATA%\APGI System\`

### macOS Issues

#### "Cannot Open Because Developer Cannot Be Verified"

**Problem:** macOS Gatekeeper blocks the application.

**Solution:**
1. Go to System Settings → Privacy & Security
2. Scroll to "Security" section
3. Click "Open Anyway" next to the APGI System message
4. Confirm by clicking "Open" in the dialog

**Alternative:**
1. Right-click (or Control-click) the application
2. Select "Open" from the menu
3. Click "Open" in the confirmation dialog

#### Application Won't Launch

**Problem:** Double-clicking does nothing or shows an error.

**Solutions:**
- Ensure you're running macOS 12 or later
- Check Console.app for error messages
- Try launching from Terminal to see errors:
  ```bash
  /Applications/APGI\ System.app/Contents/MacOS/APGI\ System
  ```
- Verify the application was copied to Applications (not run from DMG)
- Re-download and reinstall the application

#### "Damaged Application" Error

**Problem:** macOS says the application is damaged and can't be opened.

**Solution:**
1. This usually happens if the download was corrupted
2. Delete the application from Applications folder
3. Empty Trash
4. Re-download the .dmg file
5. Install again

**If problem persists:**
```bash
# Remove quarantine attribute (use with caution)
xattr -cr /Applications/APGI\ System.app
```

#### Application Crashes on Apple Silicon

**Problem:** Application crashes or shows errors on M1/M2/M3 Macs.

**Solutions:**
- Ensure you downloaded the correct version (Universal or Apple Silicon)
- Try running in Rosetta mode (Intel version on Apple Silicon)
- Check Activity Monitor for crash reports
- Ensure macOS is up to date

#### Can't Save Configuration

**Problem:** Error when trying to save configuration or export data.

**Solutions:**
- Grant Full Disk Access permission:
  1. System Settings → Privacy & Security → Full Disk Access
  2. Click the "+" button and add APGI System
- Check available disk space (need at least 100 MB free)
- Verify permissions on Application Support folder:
  ```bash
  ls -la ~/Library/Application\ Support/APGI\ System/
  ```

### General Issues

#### GUI Appears Blurry or Incorrectly Sized

**Problem:** Interface elements are too large, too small, or blurry.

**Solutions:**
- **Windows:** Check display scaling settings (Settings → Display → Scale)
- **macOS:** The application should handle Retina displays automatically
- Try adjusting your display resolution
- Restart the application after changing display settings

#### Experimental Tasks Don't Run

**Problem:** Clicking "Run" on experimental tasks does nothing or shows errors.

**Solutions:**
- Check that configuration file is valid
- Ensure sufficient RAM is available
- Look for error messages in the application log
- Try resetting to default configuration (File → Reset to Defaults)

#### Data Export Fails

**Problem:** Cannot export data or results.

**Solutions:**
- Ensure you have write permissions to the selected directory
- Choose a different export location
- Check available disk space
- Try exporting to Desktop first, then move the file

#### Application Runs Slowly

**Problem:** Application is sluggish or unresponsive.

**Solutions:**
- Close other applications to free up RAM
- Reduce the complexity of simulations
- Check CPU usage in Task Manager (Windows) or Activity Monitor (macOS)
- Ensure your computer meets minimum requirements

---

## Uninstallation

### Windows

#### If Installed with Installer:

1. Open Settings → Apps → Installed apps
2. Find "APGI System" in the list
3. Click the three dots (⋯) and select "Uninstall"
4. Follow the uninstaller wizard
5. Optionally, delete configuration files:
   - Navigate to `%APPDATA%\APGI System\`
   - Delete the folder

#### If Using Standalone Executable:

1. Simply delete the `APGI_System.exe` file
2. Delete any shortcuts you created
3. Optionally, delete configuration files:
   - Navigate to `%APPDATA%\APGI System\`
   - Delete the folder

### macOS

1. Open Finder and go to Applications
2. Find "APGI System"
3. Drag it to the Trash (or right-click → Move to Trash)
4. Empty Trash
5. Optionally, delete configuration files:
   ```bash
   rm -rf ~/Library/Application\ Support/APGI\ System/
   ```

---

## Getting Help

### Documentation

- **Build Documentation:** See `build/README_BUILD.md` for developer information
- **Configuration Guide:** See `docs/CONFIG_VALIDATION.md` for configuration details
- **API Documentation:** See `API_SETUP_GUIDE.md` for REST API usage

### Support

If you continue to experience issues:

1. **Check System Requirements:** Ensure your system meets minimum requirements
2. **Review Error Messages:** Note any error messages or codes
3. **Check Logs:**
   - Windows: `%APPDATA%\APGI System\logs\`
   - macOS: `~/Library/Application Support/APGI System/logs/`
4. **Contact Support:** Provide the following information:
   - Operating system and version
   - Application version
   - Steps to reproduce the issue
   - Error messages or screenshots
   - Log files (if available)

### Known Limitations

- The application requires an active display (cannot run headless)
- Some experimental tasks may require significant RAM (8 GB recommended)
- Network features require internet connectivity
- File paths with special characters may cause issues on some systems

---

## Additional Information

### Configuration Files

Your settings are stored in:
- **Windows:** `%APPDATA%\APGI System\config.yaml`
- **macOS:** `~/Library/Application Support/APGI System/config.yaml`

You can edit this file manually with a text editor, but be careful to maintain valid YAML syntax.

### Data Files

Exported data and results are saved to:
- **Windows:** `%USERPROFILE%\Documents\APGI System\`
- **macOS:** `~/Documents/APGI System/`

You can change the default export location in the application settings.

### Updates

To update to a new version:
1. Download the latest version
2. Uninstall the current version (optional but recommended)
3. Install the new version following the installation instructions above
4. Your configuration and data files will be preserved

### Privacy

The APGI System application:
- Does not collect or transmit personal data
- Stores all data locally on your computer
- Does not require internet connectivity (except for optional features)
- Does not include analytics or tracking

---

## Quick Reference

### File Locations

| Item | Windows | macOS |
|------|---------|-------|
| Application | `C:\Program Files\APGI System\` | `/Applications/APGI System.app` |
| Configuration | `%APPDATA%\APGI System\` | `~/Library/Application Support/APGI System/` |
| Data Export | `%USERPROFILE%\Documents\APGI System\` | `~/Documents/APGI System/` |
| Logs | `%APPDATA%\APGI System\logs\` | `~/Library/Application Support/APGI System/logs/` |

### Keyboard Shortcuts

- **Ctrl+N / Cmd+N:** New simulation
- **Ctrl+O / Cmd+O:** Open configuration
- **Ctrl+S / Cmd+S:** Save configuration
- **Ctrl+E / Cmd+E:** Export data
- **Ctrl+Q / Cmd+Q:** Quit application
- **F1:** Help documentation
- **F11:** Toggle fullscreen

---

**Version:** 1.0.0  
**Last Updated:** December 2024  
**Document:** README_DISTRIBUTION.md

For technical documentation and build instructions, see `build/README_BUILD.md`.
