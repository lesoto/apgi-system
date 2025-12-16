# APGI System Application Icons

This directory contains the application icons for the APGI System in multiple formats for cross-platform support.

## Files

- **apgi.png** - Source icon (1024x1024 PNG)
  - High-resolution source image
  - Can be used for documentation, web, or regenerating other formats

- **apgi.ico** - Windows icon
  - Multi-resolution icon file for Windows executables
  - Contains sizes: 256, 128, 64, 48, 32, 16 pixels
  - Used by PyInstaller for Windows builds

- **apgi.icns** - macOS icon
  - Multi-resolution icon file for macOS application bundles
  - Contains all standard macOS icon sizes including Retina (@2x) versions
  - Used by py2app for macOS builds

- **apgi.iconset/** - macOS iconset directory
  - Contains individual PNG files at all required sizes
  - Can be used with `iconutil` on macOS to regenerate .icns
  - Kept for reference and regeneration purposes

## Icon Design

The APGI System icon features a neural network visualization representing the consciousness modeling framework:

- **Central Node (Gold)**: Represents the "ignition" moment in consciousness
- **Inner Ring (Cyan)**: Represents precision-gated processing nodes
- **Outer Ring (Blue)**: Represents hierarchical distributed processing
- **Connections**: Represent information flow in the active inference framework

The color scheme uses professional blue/cyan tones for a scientific/technical appearance, with gold accents highlighting the "ignition" concept.

## Regenerating Icons

To regenerate all icon formats from scratch:

```bash
python build/create_icons.py
```

This will:
1. Create the source PNG (1024x1024)
2. Generate Windows .ico with multiple resolutions
3. Create macOS iconset directory with all required sizes
4. Generate macOS .icns file

To create only the .icns file from an existing iconset:

```bash
python build/create_icns.py
```

On macOS, you can also use the native `iconutil` command:

```bash
iconutil -c icns resources/icons/apgi.iconset
```

## Requirements

Icon generation requires:
- Python 3.9+
- Pillow (PIL) library

These are included in `requirements-build.txt`.

## Usage in Build Process

### Windows (PyInstaller)

The icon is specified in the PyInstaller spec file:

```python
exe = EXE(
    ...
    icon='resources/icons/apgi.ico',
    ...
)
```

### macOS (py2app)

The icon is specified in the py2app setup:

```python
OPTIONS = {
    'iconfile': 'resources/icons/apgi.icns',
    ...
}
```
