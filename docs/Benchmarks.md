# Performance Benchmarks

This directory contains comprehensive performance benchmarks for the APGI Framework.

## Structure

- `test_performance.py` (454 lines) - Main benchmark tests using pytest-benchmark
- `profiling_utils.py` (497 lines) - Advanced profiling utilities and decorators
- `conftest.py` (27 lines) - pytest configuration and fixtures
- `critical_path_profiling.py` - Critical path performance profiling

## Running Benchmarks

### Prerequisites

The benchmark system requires `pytest-benchmark` to be installed. If not available, the benchmark tests will be skipped.

```bash
pip install pytest-benchmark
```

### Basic Benchmark Run

```bash
# Run all benchmarks
pytest benchmarks/ --benchmark-only

# Run specific benchmark
pytest benchmarks/test_performance.py::TestAPGIAgentPerformance::test_agent_update_performance --benchmark-only

# Run with verbose output
pytest benchmarks/ --benchmark-only -v
```

### Advanced Profiling

```bash
# Run with memory profiling
pytest benchmarks/ --benchmark-only --benchmark-profile

# Generate benchmark report
pytest benchmarks/ --benchmark-only --benchmark-json=benchmark_results.json

# Compare with previous results
pytest benchmarks/ --benchmark-only --benchmark-compare=previous_results.json
```

### Manual Profiling

```python
from benchmarks.profiling_utils import Profiler, BenchmarkRunner

# Use profiler decorator
@Profiler().profile_function()
def my_function():
    # Your code here
    pass

# Run comprehensive benchmark
runner = BenchmarkRunner()
results = runner.run_benchmark_suite({
    'test1': my_function,
    'test2': another_function
})
```

## Benchmark Categories

### 1. APGI Agent Performance

- Agent update speed
- Memory usage over time
- Scaling with observation size

### 2. Analysis Engine Performance

- Small, medium, and large dataset analysis
- Performance scaling analysis
- Memory efficiency

### 3. Stimulus Generator Performance

- Simple vs complex stimulus generation
- Throughput measurement
- Resource usage

### 4. Data Processing Performance

- EEG data processing
- Behavioral data analysis
- Feature extraction speed

### 5. Memory Performance

- Large array allocation
- Memory cleanup verification
- Memory leak detection

## Performance Targets

### Response Time Targets

- Agent update: < 1ms
- Small data analysis: < 100ms
- Medium data analysis: < 1s
- Large data analysis: < 10s
- Stimulus generation: > 100 stimuli/second

### Memory Usage Targets

- Agent memory growth: < 10MB per 1000 updates
- Analysis memory scaling: Linear with data size
- Memory cleanup: > 90% of allocated memory freed

### Scaling Targets

- Analysis performance: < 2x time for 5x data
- Memory usage: < 2x memory for 5x data

## Results

Benchmark results are saved in the `benchmark_results/` directory:

- `*.prof` - Binary profile files
- `*.txt` - Human-readable profile statistics
- `profile_comparison.csv` - Comparison of multiple profiles
- `profiling_report.md` - Comprehensive profiling report
- `memory_usage.png` - Memory usage plot
- `system_usage.png` - System resource usage plot
- `benchmark_results.json` - pytest-benchmark results

## Continuous Integration

The benchmarks are integrated into the CI/CD pipeline:

1. **Performance Regression Detection**: Benchmarks run on every PR
2. **Performance Monitoring**: Track performance over time
3. **Alert Thresholds**: Fail build if performance degrades > 20%
4. **Historical Tracking**: Store and compare results across versions

## Best Practices

### Writing Benchmarks

1. Use realistic data sizes
2. Test both happy path and edge cases
3. Include memory usage tests
4. Test scaling behavior
5. Use meaningful benchmark names

### Analyzing Results

1. Look for performance regressions
2. Identify memory leaks
3. Check scaling behavior
4. Monitor system resource usage
5. Compare across different environments

### Performance Optimization

1. Profile before optimizing
2. Focus on hot paths
3. Consider algorithmic complexity
4. Optimize memory usage
5. Test optimizations with benchmarks

## Troubleshooting

### Common Issues

1. **Import errors**: Make sure APGI modules are properly installed
2. **Memory issues**: Reduce data sizes for memory-constrained environments
3. **Timeouts**: Increase timeout limits for slow benchmarks
4. **Inconsistent results**: Run multiple times and average
5. **pytest-benchmark not available**: Install with `pip install pytest-benchmark`

### Debug Mode

```bash
# Run with debug output
pytest benchmarks/ --benchmark-only -v -s

# Run specific test with profiling
python -m cProfile -o profile.stats benchmarks/test_performance.py
```

## Contributing

When adding new benchmarks:

1. Follow the existing naming conventions
2. Add appropriate performance targets
3. Include documentation
4. Test on different environments
5. Update this README

## References

- [pytest-benchmark documentation](https://pytest-benchmark.readthedocs.io/)
- [cProfile documentation](https://docs.python.org/3/library/profile.html)
- [memory_profiler documentation](https://pypi.org/project/memory-profiler/)
- [psutil documentation](https://psutil.readthedocs.io/)
