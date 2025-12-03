"""Quick test to verify performance monitoring functionality."""

import numpy as np
from apgi_system.system import APGISystem


def test_performance_monitoring():
    """Test that performance monitoring works correctly."""
    print("Testing performance monitoring...")
    
    # Create system
    system = APGISystem()
    
    # Run a few steps
    for i in range(5):
        extero_input = np.random.randn(256) * 0.5
        state = system.step(extero_input)
        
        # Check that performance metrics are in the state
        assert "performance" in state, "Performance metrics not in state"
        perf = state["performance"]
        
        print(f"\nStep {i+1}:")
        print(f"  Step time: {perf['step_time_ms']:.3f} ms")
        print(f"  Memory usage: {perf['memory_usage_mb']:.1f} MB")
        print(f"  Ignition rate: {perf['ignition_rate_hz']:.2f} Hz")
    
    # Get performance statistics
    stats = system.get_performance_statistics()
    print("\n=== Performance Statistics ===")
    print(f"Total samples: {stats['total_samples']}")
    print(f"Mean step time: {stats['mean_step_time_ms']:.3f} ms")
    print(f"Max step time: {stats['max_step_time_ms']:.3f} ms")
    print(f"Mean memory: {stats['mean_memory_mb']:.1f} MB")
    print(f"Max memory: {stats['max_memory_mb']:.1f} MB")
    
    # Test logging
    print("\n=== Testing log_performance ===")
    system.log_performance(verbose=True)
    
    # Test reset
    system.reset()
    stats_after_reset = system.get_performance_statistics()
    assert stats_after_reset['total_samples'] == 0, "Reset didn't clear history"
    print("\n✓ Reset works correctly")
    
    print("\n✓ All performance monitoring tests passed!")


if __name__ == "__main__":
    test_performance_monitoring()
