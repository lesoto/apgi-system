# ADR 0002: Mock Module Refactoring

## Status
Accepted

## Context
Mock-like modules (`cache.py` and `network.py`) were located in the top-level `apgi_framework/` package path, diluting architectural consistency. These modules were labeled as "Mock classes for testing purposes" but were imported in production code (`main_controller.py`).

## Decision
Move mock modules to test-only location:
1. Move `apgi_framework/cache.py` to `tests/fixtures/mock_cache.py`
2. Move `apgi_framework/network.py` to `tests/fixtures/mock_network.py`
3. Update imports in `main_controller.py` to reference new location
4. Update test mocks to use new location

## Consequences
### Positive
- Clear separation between production code and test fixtures
- Improved architectural consistency
- Better code organization and maintainability
- Reduces confusion about module purpose

### Negative
- Mock modules still used in production code (execute_network_intensive_operations method)
- Requires further work to define production interfaces with concrete implementations
- Import paths now cross package boundary (tests/fixtures -> apgi_framework)

### Alternatives Considered
1. **Delete mock modules entirely**: Would break existing functionality
2. **Keep in production path**: Chosen against due to architectural inconsistency
3. **Create production interfaces first**: Deferred as larger refactoring effort

## References
- Files modified: `apgi_framework/main_controller.py`, `tests/test_end_to_end_workflow.py`
- Files moved: `apgi_framework/cache.py` → `tests/fixtures/mock_cache.py`, `apgi_framework/network.py` → `tests/fixtures/mock_network.py`
- Related: TODO item #3 (Refactor mock modules)
