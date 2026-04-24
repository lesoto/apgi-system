"""
Test script for pupillometry and physiological monitoring systems.

This script demonstrates the functionality of the PupillometryInterface
and PhysiologicalMonitoring classes.
"""

import time

import numpy as np

from apgi_framework.neural.physiological_monitoring import (
    PhysiologicalConfig,
    PhysiologicalMonitoring,
    SignalType,
)
from apgi_framework.neural.pupillometry_interface import (
    BlinkDetectionMethod,
    EyeType,
    PupillometryConfig,
    PupillometryInterface,
)


def test_pupillometry_interface() -> None:
    """Test pupillometry interface functionality."""
    print("=" * 60)
    print("Testing PupillometryInterface")
    print("=" * 60)

    # Create configuration
    config = PupillometryConfig(
        sampling_rate=500.0,
        buffer_size=5000,
        eye_tracked=EyeType.BOTH,
        blink_detection_method=BlinkDetectionMethod.COMBINED,
        enable_luminance_correction=True,
    )

    # Initialize interface
    pupil_interface = PupillometryInterface(config)

    # fmt: off
    print(
        f"✓ Created PupillometryInterface with {config.sampling_rate} "
        "Hz sampling"
    )
    # fmt: on

    # Start streaming with simulated data
    print("✓ Starting data streaming.")
    pupil_interface.start_streaming()

    # Let it collect some data
    time.sleep(2.0)

    # Get buffer data
    samples = pupil_interface.get_buffer_data(n_samples=100)
    print(f"✓ Collected {len(samples)} samples")

    # Process data
    print("✓ Processing pupillometry data.")
    processed = pupil_interface.process_data(
        samples=samples,
        apply_blink_detection=True,
        apply_artifact_correction=True,
        apply_baseline_correction=True,
        apply_luminance_correction=True,
    )

    print(f"  - Raw diameters: {len(processed['raw_diameters'])} samples")
    print(f"  - Blinks detected: {np.sum(processed['blinks'])}")
    print(f"  - Artifacts detected: {np.sum(processed['artifacts'])}")
    baseline_value = (
        np.mean(processed["baseline"])
        if isinstance(processed["baseline"], np.ndarray)
        else processed["baseline"]
    )
    print(f"  - Baseline: {baseline_value:.3f} mm")

    # Get quality metrics
    quality = pupil_interface.get_quality_metrics()
    print(f"✓ Data quality: {quality['status']}")
    print(f"  - Quality score: {quality['quality_score']:.3f}")
    print(f"  - Mean confidence: {quality['mean_confidence']:.3f}")
    print(f"  - Blink rate: {quality['blink_rate']:.3f}")

    # Stop streaming
    pupil_interface.stop_streaming()
    print("✓ Stopped streaming")

    # Export data
    try:
        pupil_interface.export_data("test_pupil_data.npz", format="numpy")
        print("✓ Exported data to test_pupil_data.npz")
    except Exception as e:
        print(f"  Export skipped: {e}")

    print("\n✓ PupillometryInterface test completed successfully!\n")


def test_physiological_monitoring() -> None:
    """Test physiological monitoring functionality."""
    print("=" * 60)
    print("Testing PhysiologicalMonitoring")
    print("=" * 60)

    # Create configuration
    config = PhysiologicalConfig(
        sampling_rate=500.0,
        buffer_size=5000,
        enable_ecg=True,
        enable_scr=True,
        enable_respiration=True,
        enable_synchronization=True,
    )

    # Initialize monitoring system
    physio_monitor = PhysiologicalMonitoring(config)

    # fmt: off
    print(
        f"✓ Created PhysiologicalMonitoring with {config.sampling_rate} "
        "Hz sampling"
    )
    # fmt: on

    # Register callback for real-time processing
    def data_callback(sample):
        """Example callback for real-time data."""
        pass  # In real use, this would process data in real-time

    physio_monitor.register_callback(data_callback)
    print("✓ Registered data callback")

    # Start streaming with simulated data
    print("✓ Starting multi-modal data streaming.")
    physio_monitor.start_streaming()

    # Let it collect some data
    time.sleep(2.0)

    # Get buffer data
    samples = physio_monitor.get_buffer_data(n_samples=100)
    print(f"✓ Collected {len(samples)} integrated samples")

    # Get specific signal data
    # fmt: off
    ecg_data, ecg_times = physio_monitor.get_signal_data(
        SignalType.ECG, n_samples=500
    )
    # fmt: on
    # fmt: off
    scr_data, scr_times = physio_monitor.get_signal_data(
        SignalType.SCR, n_samples=500
    )
    # fmt: on
    resp_data, resp_times = physio_monitor.get_signal_data(SignalType.RESP, n_samples=500)

    print("✓ Retrieved signal data:")
    print(f"  - ECG: {len(ecg_data)} samples")
    print(f"  - SCR: {len(scr_data)} samples")
    print(f"  - Respiration: {len(resp_data)} samples")

    # Compute comprehensive metrics
    print("✓ Computing comprehensive metrics.")
    metrics = physio_monitor.compute_comprehensive_metrics()

    if "heart_rate" in metrics:
        print(f"  - Heart rate: {metrics['heart_rate']:.1f} bpm")
        if "hrv" in metrics:
            hrv = metrics["hrv"]
            if isinstance(hrv, dict):
                print(f"  - HRV SDNN: {hrv.get('sdnn', 0):.2f} ms")
                print(f"  - HRV RMSSD: {hrv.get('rmssd', 0):.2f} ms")
            else:
                print(f"  - HRV: {hrv:.2f} ms")

    if "scr_level" in metrics:
        print(f"  - SCR level: {metrics['scr_level']:.3f} μS")
        print(f"  - SCR events: {metrics['scr_events']}")
        print(f"  - SCR rate: {metrics['scr_rate']:.2f} events/min")

    if "respiration_rate" in metrics:
        # fmt: off
        print(
            f"  - Respiration rate: {metrics['respiration_rate']:.1f} "
            "breaths/min"
        )
        # fmt: on
        print(f"  - Current phase: {metrics.get('current_phase', 'unknown')}")

    # Test synchronization
    print("✓ Testing synchronization.")
    external_time = time.time()
    synced_sample = physio_monitor.synchronize_with_external(external_time)
    if synced_sample:
        print("  - Found synchronized sample within tolerance")

    # Get quality metrics
    quality = physio_monitor.get_quality_metrics()
    print(f"✓ Data quality: {quality['status']}")
    print(f"  - Overall quality: {quality['overall_quality']:.3f}")
    print(f"  - Heart rate quality: {quality['heart_rate_quality']:.3f}")
    print(f"  - SCR quality: {quality['scr_quality']:.3f}")
    print(f"  - Respiration quality: {quality['respiration_quality']:.3f}")

    # Stop streaming
    physio_monitor.stop_streaming()
    print("✓ Stopped streaming")

    # Export data
    try:
        physio_monitor.export_data("test_physio_data.npz", format="numpy")
        print("✓ Exported data to test_physio_data.npz")
    except Exception as e:
        print(f"  Export skipped: {e}")

    print("\n✓ PhysiologicalMonitoring test completed successfully!\n")


def test_integration():
    """Test integration of pupillometry and physiological monitoring."""
    print("=" * 60)
    print("Testing Integrated Multi-Modal Monitoring")
    print("=" * 60)

    # Create both systems
    pupil_config = PupillometryConfig(sampling_rate=500.0)
    physio_config = PhysiologicalConfig(sampling_rate=500.0)

    pupil_interface = PupillometryInterface(pupil_config)
    physio_monitor = PhysiologicalMonitoring(physio_config)

    print("✓ Created both monitoring systems")

    # Start both systems
    pupil_interface.start_streaming()
    physio_monitor.start_streaming()
    print("✓ Started synchronized streaming")

    # Collect data
    time.sleep(2.0)

    # Get synchronized data
    pupil_samples = pupil_interface.get_buffer_data(n_samples=50)
    physio_samples = physio_monitor.get_buffer_data(n_samples=50)

    print("✓ Collected synchronized data:")
    print(f"  - Pupil samples: {len(pupil_samples)}")
    print(f"  - Physiological samples: {len(physio_samples)}")

    # Test temporal synchronization
    if pupil_samples and physio_samples:
        pupil_time = pupil_samples[-1].timestamp
        synced_physio = physio_monitor.synchronize_with_external(pupil_time)

        if synced_physio:
            time_diff = abs(synced_physio.timestamp - pupil_time) * 1000.0
            print("✓ Synchronization successful:")
            print(f"  - Time difference: {time_diff:.2f} ms")

    # Stop both systems
    pupil_interface.stop_streaming()
    physio_monitor.stop_streaming()
    print("✓ Stopped both systems")

    print("\n✓ Integration test completed successfully!\n")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("APGI Framework - Pupillometry & Physiological Monitoring Tests")
    print("=" * 60 + "\n")

    try:
        # Test pupillometry
        test_pupillometry_interface()

        # Test physiological monitoring
        test_physiological_monitoring()

        # Test integration
        test_integration()

        print("=" * 60)
        print("ALL TESTS PASSED!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()
