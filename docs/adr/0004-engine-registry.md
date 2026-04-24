# ADR 0004: Centralized Engine Registry

## Status
Accepted

## Context
The APGI Framework had engine implementations scattered across multiple modules (core/, engines/, analysis/). This led to:
- Inconsistent initialization patterns across engines
- Difficulty discovering available engines
- No unified lifecycle management
- Duplicate code for engine configuration
- Hard to test and mock engines

## Decision
Implement a centralized Engine Registry pattern (`apgi_framework.engines`) that:
1. Provides singleton `EngineRegistry` for engine discovery and lifecycle
2. Defines `EngineMetadata` for declarative engine registration
3. Uses `EngineType` enum for categorization
4. Supports lazy instantiation with singleton caching
5. Provides dependency tracking per engine
6. Enables runtime engine registration/unregistration

## Architecture

```
apgi_framework/engines/
├── __init__.py          # EngineRegistry, EngineMetadata, EngineType
├── equation_engine.py   # APGIEquation implementation
├── precision_engine.py # PrecisionCalculator
├── prediction_error_engine.py # PredictionErrorProcessor
├── somatic_marker_engine.py # SomaticMarkerEngine
├── threshold_engine.py  # ThresholdManager
└── models_engine.py     # PredictiveIgnitionNetwork, SomaticAgent
```

## Consequences

### Positive
- Unified engine discovery via `EngineRegistry.get_engine(name)`
- Consistent configuration pattern across all engines
- Centralized dependency management
- Easy to mock engines for testing
- Clear extension point for new engines
- Type-safe engine access

### Negative
- Additional abstraction layer may increase complexity
- Singleton pattern can make testing harder in some cases
- Requires documentation for engine authors

### Alternatives Considered
1. **Module-level functions**: Too scattered, no lifecycle management
2. **Dependency injection framework**: Too heavy, adds external dependency
3. **Plugin system**: Overkill for current needs, registry pattern sufficient

## Usage

```python
from apgi_framework.engines import EngineRegistry

registry = EngineRegistry()
equation_engine = registry.create_engine("equation")
precision_calc = registry.create_engine("precision", config={"default_precision": 0.95})
```

## References
- Files: `apgi_framework/engines/__init__.py`, `apgi_framework/engines/*_engine.py`
- Tests: `tests/test_engines_registry.py`
- Related: Main controller engine initialization
