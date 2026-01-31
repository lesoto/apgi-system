# APGI System Accessibility Guide

This document provides information about accessibility features and keyboard navigation in the APGI System GUI applications.

## Screen Reader Support

The APGI System GUI applications are built with Tkinter, which provides basic screen reader support. To improve accessibility:

- Ensure your screen reader is running before launching the GUI
- Use Tab and Shift+Tab to navigate between controls
- Most interactive elements have descriptive labels

## Keyboard Navigation

### Global Shortcuts

- **Ctrl/Cmd + Q**: Quit application
- **Ctrl/Cmd + N**: New session (apgi_gui.py)
- **Ctrl/Cmd + O**: Open configuration (apgi_gui.py)
- **Ctrl/Cmd + S**: Save configuration (apgi_gui.py)
- **Ctrl/Cmd + E**: Export data (apgi_gui.py)
- **Ctrl/Cmd + R**: Reset simulation (apgi_gui.py)
- **F5**: Start simulation (apgi_gui.py)
- **F6**: Pause/Resume simulation (apgi_gui.py)
- **F7**: Stop simulation (apgi_gui.py)
- **F8**: Reset simulation (apgi_gui.py)
- **F1**: Show help (apgi_gui.py)

### Navigation

- **Tab**: Move focus to next control
- **Shift+Tab**: Move focus to previous control
- **Enter/Return**: Activate focused button or control
- **Escape**: Close dialogs or cancel operations

## High Contrast Mode

While the APGI System does not currently have a built-in high contrast mode, you can:

1. Use your operating system's high contrast settings
2. Adjust theme colors in the configuration file (if theme support is available)

## Font Scaling

To adjust font sizes:

1. Use your operating system's display scaling settings
2. For event logs, all GUIs now use consistent Courier 9pt font

## Known Accessibility Limitations

- No built-in screen reader announcements for dynamic content updates
- Limited keyboard navigation for complex visualizations
- No built-in high contrast theme
- Tooltips may not be readable by all screen readers

## Improving Accessibility

To improve accessibility in future versions, consider:

- Adding ARIA-like labels to interactive elements
- Implementing screen reader announcements for status updates
- Adding keyboard shortcuts for all common operations
- Supporting high contrast themes
- Improving focus indicators

## Feedback

If you encounter accessibility issues or have suggestions for improvement, please report them in the project's issue tracker.
