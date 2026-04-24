# ADR 0006: CLI Smoke Testing Strategy

## Status
Accepted

## Context
The APGI Framework has multiple entry points:
- `apgi_framework.cli` - Main CLI module
- `apgi_gui.cli` - GUI launcher
- `apgi_framework.testing.main` - Test runner
- Multiple GUI scripts (APGI_GUI.py, GUI-Launcher.py)

Need to verify:
- All entry points can be imported
- Core workflow executes without errors
- Integration between components works
- No import cycles or missing dependencies

## Decision
Implement two-tier CLI smoke testing:

### Tier 1: Import Smoke Tests
Verify all major modules can be imported:
```python
def test_core_imports():
    imports = [
        ("apgi_framework.exceptions", "APGIFrameworkError"),
        ("apgi_framework.config.constants", "ModelConstants"),
        ("apgi_framework.core.data_models", "APGIParameters"),
    ]
    for module, attr in imports:
        mod = __import__(module, fromlist=[attr])
        assert hasattr(mod, attr)
```

### Tier 2: End-to-End Workflow Test
Run minimal experiment through Python API:
```python
def test_minimal_experiment_workflow():
    from core.experiment import BaseExperiment
    
    class SimpleTestExperiment(BaseExperiment):
        def run_trial(self, participant_id, trial_params):
            return {"participant_id": participant_id, "result": "success"}
    
    exp = SimpleTestExperiment(n_participants=2)
    data = exp.run_experiment()
    assert len(data) == 2
```

## Consequences

### Positive
- Fast feedback on broken imports
- No subprocess overhead for most tests
- Can run in CI without full GUI environment
- Catches integration issues early

### Negative
- Not testing actual subprocess behavior
- GUI tests may still fail in headless environments
- Limited coverage of CLI argument parsing

### Alternatives Considered
1. **Subprocess-based testing**: Slower, more realistic but impractical for unit tests
2. **Full integration tests**: Covered separately in `tests/integration/`
3. **Click/Typer testing framework**: Not needed for current CLI structure

## References
- Files: `tests/test_cli_smoke.py`, `apgi_framework/cli.py`, `apgi_gui/cli.py`
- Related: Integration tests, CI/CD pipeline
