# Screenshots for Distribution Documentation

This directory contains screenshots referenced in `README_DISTRIBUTION.md`.

## Required Screenshots

### Windows Installation

1. **windows_download.png**
   - Browser showing the download of `APGI_System_Setup.exe`
   - Should show the file being saved to Downloads folder

2. **windows_smartscreen.png**
   - Windows SmartScreen warning dialog (if applicable)
   - Should show "More info" and "Run anyway" options

3. **windows_installer_wizard.png**
   - Inno Setup installer wizard
   - Should show installation options (desktop shortcut, Start Menu entry)

4. **windows_install_complete.png**
   - Installation completion screen
   - Should show "Finish" button and "Launch APGI System" checkbox

5. **windows_app_running.png**
   - APGI System main window running on Windows
   - Should show the full application interface

### macOS Installation

1. **macos_download.png**
   - Browser showing the download of `APGI_System.dmg`
   - Should show the file being saved to Downloads folder

2. **macos_dmg_window.png**
   - Mounted DMG window
   - Should show APGI System icon and Applications folder shortcut
   - Should display custom background if configured

3. **macos_drag_install.png**
   - Screenshot showing the drag-and-drop installation process
   - Should show cursor dragging app icon to Applications folder

4. **macos_applications.png**
   - Finder window showing Applications folder
   - Should highlight APGI System in the list

5. **macos_gatekeeper.png**
   - macOS Gatekeeper security warning
   - Should show "cannot be opened because it is from an unidentified developer" message

6. **macos_privacy_settings.png**
   - System Settings → Privacy & Security
   - Should show "APGI System was blocked" message and "Open Anyway" button

7. **macos_app_running.png**
   - APGI System main window running on macOS
   - Should show the full application interface

## Screenshot Guidelines

### General Requirements

- **Resolution:** Minimum 1280x720, preferably 1920x1080
- **Format:** PNG (preferred) or JPEG
- **Quality:** High quality, no compression artifacts
- **Content:** Clear, readable text and UI elements
- **Privacy:** Remove any personal information (usernames, file paths, etc.)

### Platform-Specific Guidelines

**Windows:**

- Use Windows 10 or 11 with default theme
- Ensure taskbar and window decorations are visible
- Capture full windows, not just portions

**macOS:**

- Use macOS 12 or later with default theme
- Ensure menu bar and window decorations are visible
- Capture full windows, not just portions
- Consider both light and dark mode if applicable

### Capturing Screenshots

**Windows:**

- Use Snipping Tool (Windows 10) or Snip & Sketch (Windows 11)
- Or press `Win + Shift + S` for quick capture
- Save as PNG format

**macOS:**

- Press `Cmd + Shift + 4` then `Space` to capture a window
- Or press `Cmd + Shift + 3` to capture full screen
- Screenshots automatically save to Desktop as PNG

### Editing Screenshots

- Add arrows or highlights to draw attention to important elements
- Use red or yellow for highlights (ensure good contrast)
- Add text annotations if needed to clarify steps
- Keep editing minimal and professional
- Use tools like:
  - Windows: Paint, Paint 3D, or Snip & Sketch
  - macOS: Preview, Markup tools
  - Cross-platform: GIMP, Inkscape

## File Naming Convention

Use the exact filenames specified in `README_DISTRIBUTION.md`:

- Use lowercase letters
- Use underscores for spaces
- Use `.png` extension
- Be descriptive but concise

## Updating Screenshots

When updating the application:

1. Recapture all screenshots with the new version
2. Ensure version numbers match (if visible)
3. Update any UI changes reflected in screenshots
4. Verify all screenshot references in `README_DISTRIBUTION.md` are still accurate

## Alternative: Placeholder Images

If actual screenshots are not yet available, you can create placeholder images:

```bash
# Create placeholder images (requires ImageMagick)
convert -size 1280x720 xc:lightgray -pointsize 48 -fill black \
  -gravity center -annotate +0+0 "Screenshot Placeholder\nwindows_download.png" \
  windows_download.png
```

## Checklist

Before finalizing documentation:

- [ ] All 12 screenshots captured
- [ ] Screenshots are high quality and clear
- [ ] Personal information removed
- [ ] Files named correctly
- [ ] Files saved in this directory
- [ ] Screenshots referenced correctly in README_DISTRIBUTION.md
- [ ] Screenshots tested in documentation (links work)
- [ ] Screenshots show current version of application

---

**Note:** This directory should be included in the distribution package or hosted online if the documentation is web-based.
