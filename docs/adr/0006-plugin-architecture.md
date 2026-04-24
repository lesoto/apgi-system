# ADR 0006: Plugin Architecture for Custom Engines

## Status

Accepted

## Context

Users need to extend APGI with custom simulation engines without modifying core code. A plugin system is needed to support third-party extensions.

## Decision

We will implement a plugin architecture using Python entry points for engine registration.

## Consequences

### Positive

- Third-party engine support
- Clean separation between core and extensions
- Standard Python packaging for plugins
- Lazy loading of plugins

### Negative

- Dependency management complexity
- Version compatibility challenges
- Security considerations for third-party code

## Implementation

Created `apgi_framework/plugins/` module with:
- `PluginRegistry`: Entry point-based discovery
- `EngineInterface`: Abstract base class for engines
- `PluginManager`: Lifecycle and configuration management
- `PluginSpec`: Plugin metadata specification

## Entry Point Convention

Plugins register via `pyproject.toml`:
```toml
[project.entry-points."apgi.engines"]
custom_engine = "my_package.plugin:get_plugin_spec"
```
