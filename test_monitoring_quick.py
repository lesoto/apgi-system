"""Quick test to verify performance monitoring works."""

import numpy as np
from apgi_system.system import APGISystem

def test_performance_monitoring():
    """Test that performance monitoring is integrated and working."""
    # Create system
    system = APGISystem()
    
    # Run a few steps
    for i in range(5):
        extero_input = np.random.randn(256) * 0.5
        state = system.step(extero_input)
        
        # Check that performance metrics are in the state
        assert "performance" in state, "Performance metrics not in state"
        assert "step_time_ms" in state["performance"]
        assert "memory_usage_mb" in state["performance"]
        assert "ignition_rate_hz" in state["performance"]
        
        # Check that values are reasonable
        assert state["performance"]["step_time_ms"] > 0
        assert state["performance"]["memory_usage_mb"] > 0
        assert state["performance"]["ignition_rate_hz"] >= 0
        
        print(f"Step {i+1}: {state['performance']['step_time_ms']:.3f}ms, "
              f"{state['performance']['memory_usage_mb']:.1f}MB, "
              f"{state['performance']['ignition_rate_hz']:.2f}Hz")
    
    # Get performance statistics
    stats = system.get_performance_statistics()
    print(f"\nPerformance Statistics:")
    print(f"  Mean step time: {stats['mean_step_time_ms']:.3f}ms")
    print(f"  Max step time: {stats['max_step_time_ms']:.3f}ms")
    print(f"  Mean memory: {stats['mean_memory_mb']:.1f}MB")
    print(f"  Total samples: {stats['total_samples']}")
    
    # Test log_performance method
    print("\nLogging performance:")
    system.log_performance(verbose=True)
    
    # Test reset
    system.reset()
    stats_after_reset = system.get_performance_statistics()
    assert stats_after_reset['total_samples'] == 0, "Performance monitor not reset"
    
    print("\n✓ All performance monitoring tests passed!")

if __name__ == "__main__":
    test_performance_monitoring()
