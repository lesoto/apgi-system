# ADR 0003: Strict MyPy Enforcement in CI

## Status
Accepted

## Context
The APGI Framework had mypy type checking configured but not strictly enforced:
- mypy ran with `continue-on-error: true` in CI
- pyproject.toml had `strict = false` with phased strictness planned
- Type errors could pass without blocking CI pipelines
- Code quality gates were not truly enforced

## Decision
Enable strict mypy enforcement:
1. Set `strict = true` in pyproject.toml [tool.mypy]
2. Remove `continue-on-error: true` from mypy step in CI workflow
3. Remove `--no-strict-optional` flag (strict_optional already enabled)
4. Allow CI to fail on type errors, enforcing type safety

## Consequences
### Positive
- Type errors are caught before deployment
- Improved code quality and maintainability
- Better IDE support with accurate type hints
- Catches potential runtime errors at type-check time
- Aligns with modern Python best practices

### Negative
- Existing code with type errors will block CI
- Requires fixing many type errors (40+ errors revealed)
- May slow down development during initial fix period
- Some third-party libraries may need type stubs

### Alternatives Considered
1. **Keep phased approach**: Would never reach strict enforcement
2. **Add type ignore comments**: Chosen as interim measure for specific issues
3. **Use separate type-checking job**: More complex, single job simpler

## References
- Files modified: `.github/workflows/test.yml`, `pyproject.toml`
- Related: TODO item #7 (Enforce code quality gates)
