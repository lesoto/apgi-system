# ADR 0004: Multiprocessing for CPU-Bound Simulations

## Status

Accepted

## Context

The APGI framework performs computationally intensive neural simulations that are CPU-bound. The existing implementation runs simulations sequentially, which limits throughput when processing large batches of experiments.

## Decision

We will implement a multiprocessing module using Python's `ProcessPoolExecutor` to parallelize CPU-bound simulation workloads.

## Consequences

### Positive

- Improved throughput for batch simulations
- Better utilization of multi-core systems
- Non-blocking execution for simulation management

### Negative

- Increased memory usage per worker process
- Added complexity for shared state management
- Serialization overhead for passing data between processes

## Implementation

Created `apgi_framework/parallel/` module with:
- `ProcessPoolManager`: Manages worker pool lifecycle
- `ParallelBatchProcessor`: High-level batch processing interface
- Automatic chunking and progress tracking

## Alternatives Considered

- **Threading**: Not suitable due to Python GIL
- **asyncio**: Better for I/O-bound tasks
- **Ray/Dask**: Too heavy dependency for current needs
