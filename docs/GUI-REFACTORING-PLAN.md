# GUI Refactoring Plan

## Current State

- `Assistant-GUI.py`: 8,374 lines (monolithic)
- `apgi_gui.py`: 3,945 lines (monolithic)

## Target Structure

```text
gui/
  ├── main.py (entry point, ~200 lines)
  ├── widgets/
  │   ├── __init__.py
  │   ├── control_panel.py
  │   ├── visualization.py
  │   ├── status_bar.py
  │   └── data_display.py
  ├── dialogs/
  │   ├── __init__.py
  │   ├── settings.py
  │   ├── export.py
  │   └── about.py
  ├── utils/
  │   ├── __init__.py
  │   ├── data_formatting.py
  │   ├── plotting.py
  │   └── config.py
  └── styles/
      ├── __init__.py
      └── themes.py
```

## Migration Strategy

- Create modular directory structure
- Extract utility functions first (lowest risk)
- Create base widget classes
- Extract visualization components
- Extract control panel logic
- Extract dialog windows
- Break down main application logic
- Implement proper separation of concerns
- Add comprehensive tests
- Maintain backward compatibility during transition
- Use dependency injection for component communication
- Implement proper event handling between components
- Add comprehensive documentation for each module
