# ADR 0005: Standardized Data Models with Validation

## Status
Accepted

## Context
The APGI Framework needed consistent data structures across:
- Experimental datasets with metadata
- Query/filter operations
- Storage and persistence
- API serialization
- Analysis pipelines

Previous ad-hoc dictionaries led to:
- Inconsistent field naming
- No type safety
- Validation scattered across modules
- Difficult to track data lineage

## Decision
Implement standardized data models in `apgi_framework.data.data_models` using:
1. Dataclasses for immutable data structures
2. Pydantic-style validation hooks
3. Centralized `ExperimentMetadata` for all experiments
4. `QueryFilter` for standardized querying
5. `StorageStats` for storage analytics
6. Version tracking with `DataVersion`
7. Backup tracking with `BackupInfo`

## Key Models

```python
@dataclass
class ExperimentMetadata:
    experiment_id: str
    experiment_name: str
    researcher: str
    institution: str
    created_at: datetime
    n_participants: int
    n_trials: int
    conditions: List[str]
    # ... 20+ standardized fields

@dataclass
class ExperimentalDataset:
    metadata: ExperimentMetadata
    data: Dict[str, Any]
    raw_data: Optional[Any]
    processed_data: Optional[Any]
    analysis_results: Optional[Dict[str, Any]]
    backup_info: List[BackupInfo]
```

## Consequences

### Positive
- Type-safe data handling throughout framework
- Consistent metadata across all experiments
- Built-in validation via dataclass constructors
- Easy serialization/deserialization
- Clear data contracts between modules
- Simplified testing with predictable structures

### Negative
- More verbose than simple dictionaries
- Changes require updates across multiple modules
- Some overhead from dataclass creation

### Alternatives Considered
1. **Pydantic models**: Chose dataclasses for lighter dependency footprint
2. **Simple dictionaries**: Rejected due to lack of type safety
3. **SQLAlchemy models**: Too heavy for non-database uses

## References
- Files: `apgi_framework/data/data_models.py`, `apgi_framework/data/storage_manager.py`
- Tests: `tests/test_data_models_comprehensive.py`
- Related: Storage manager, persistence layer
