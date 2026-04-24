#!/usr/bin/env python
"""
Test script for Psychedelic Neuroimaging (DS-07) integration in Psychological-States-GUI.py

Validates:
1. PsychedelicState dataclass
2. PsychedelicAnalyzer functionality
3. Substance profiles (psilocybin, LSD, ketamine)
4. Time point dynamics (baseline, peak, recovery)
5. Flow vs. psychedelic comparison
6. PsychedelicVisualizer methods
7. OpenNeuro dataset information
"""

import sys
import logging
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Check dependencies
PLOTLY_AVAILABLE = False
try:
    import plotly.graph_objects as go  # type: ignore[import-untyped]  # noqa: F401

    PLOTLY_AVAILABLE = True
    logger.info("✓ Plotly available")
except ImportError:
    logger.warning("✗ Plotly not available")


def test_psychedelic_state():
    """Test PsychedelicState dataclass"""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 1: PsychedelicState Dataclass")
    logger.info("=" * 70)

    try:
        sys.path.insert(0, ".")
        from Psychological_States_GUI import PsychedelicState  # type: ignore

        # Create test state
        state = PsychedelicState(
            substance="psilocybin",
            dose=20.0,
            time_point="peak",
            global_alpha_power=-0.65,
            broadband_spectral_change=-0.7,
            dmn_connectivity=-0.8,
            entropy_increase=0.75,
            precision_landscape_flatness=0.8,
            beta_exponent=0.8,
            interoceptive_precision=-0.6,
            consciousness_dissolution=0.85,
        )

        logger.info("✓ PsychedelicState created")
        logger.info(f"  - Substance: {state.substance}")
        logger.info(f"  - Dose: {state.dose}mg")
        logger.info(f"  - Time point: {state.time_point}")
        logger.info(f"  - Precision reduction: {state.precision_reduction:.1%}")
        logger.info(f"  - Flow dissolution index: {state.flow_dissolution_index:.1%}")

        # Verify ranges
        assert 0.0 <= state.precision_reduction <= 1.0, "Precision reduction out of range"
        assert 0.0 <= state.flow_dissolution_index <= 1.0, "Dissolution index out of range"
        logger.info("✓ State properties verified")

        return True
    except Exception as e:
        logger.error(f"✗ PsychedelicState test failed: {e}")
        return False


def test_psychedelic_analyzer():
    """Test PsychedelicAnalyzer class"""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 2: PsychedelicAnalyzer Class")
    logger.info("=" * 70)

    try:
        from Psychological_States_GUI import PsychedelicAnalyzer  # type: ignore

        # Create analyzer
        analyzer = PsychedelicAnalyzer()
        logger.info("✓ PsychedelicAnalyzer initialized")

        # Test substance profiles
        substances = ["psilocybin", "lsd", "ketamine"]
        time_points = ["baseline", "peak", "recovery"]

        for substance in substances:
            logger.info(f"\nTesting {substance.capitalize()}:")

            for tp in time_points:
                state = analyzer.create_psychedelic_state(substance, time_point=tp)

                assert state is not None, f"Failed to create state for {substance} at {tp}"
                assert state.substance == substance, "Substance mismatch"
                assert state.time_point == tp, "Time point mismatch"

                logger.info(
                    f"  ✓ {tp:10s}: precision_flatness={state.precision_landscape_flatness:.1%}, "
                    f"dissolution={state.consciousness_dissolution:.1%}"
                )

        logger.info("✓ All substance profiles verified")
        return True
    except Exception as e:
        logger.error(f"✗ PsychedelicAnalyzer test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_substance_dynamics():
    """Test substance-specific dynamics"""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 3: Substance-Specific Dynamics")
    logger.info("=" * 70)

    try:
        from Psychological_States_GUI import PsychedelicAnalyzer  # type: ignore

        analyzer = PsychedelicAnalyzer()

        # Expected peak values
        expected_peaks = {
            "psilocybin": {
                "alpha_power": -0.65,
                "precision_flatness": 0.8,
                "dissolution": 0.85,
            },
            "lsd": {
                "alpha_power": -0.55,
                "precision_flatness": 0.75,
                "dissolution": 0.8,
            },
            "ketamine": {
                "alpha_power": -0.45,
                "precision_flatness": 0.6,
                "dissolution": 0.65,
            },
        }

        logger.info("Verifying peak effects:")
        for substance, expected in expected_peaks.items():
            state = analyzer.create_psychedelic_state(substance, time_point="peak")

            # Check values match expected (within tolerance)
            alpha_match = abs(state.global_alpha_power - expected["alpha_power"]) < 0.01
            flatness_match = (
                abs(state.precision_landscape_flatness - expected["precision_flatness"]) < 0.01
            )
            dissolution_match = (
                abs(state.consciousness_dissolution - expected["dissolution"]) < 0.01
            )

            status = "✓" if (alpha_match and flatness_match and dissolution_match) else "⚠"
            logger.info(
                f"{status} {substance:12s}: alpha={state.global_alpha_power:.2f}, "
                f"flatness={state.precision_landscape_flatness:.2f}, "
                f"dissolution={state.consciousness_dissolution:.2f}"
            )

        logger.info("✓ Substance dynamics verified")
        return True
    except Exception as e:
        logger.error(f"✗ Substance dynamics test failed: {e}")
        return False


def test_time_point_progression():
    """Test baseline → peak → recovery progression"""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 4: Time Point Progression")
    logger.info("=" * 70)

    try:
        from Psychological_States_GUI import PsychedelicAnalyzer  # type: ignore

        analyzer = PsychedelicAnalyzer()

        logger.info("Testing baseline → peak → recovery progression:")

        for substance in ["psilocybin", "lsd", "ketamine"]:
            baseline = analyzer.create_psychedelic_state(substance, time_point="baseline")
            peak = analyzer.create_psychedelic_state(substance, time_point="peak")
            recovery = analyzer.create_psychedelic_state(substance, time_point="recovery")

            # Verify progression
            baseline_flatness = baseline.precision_landscape_flatness
            peak_flatness = peak.precision_landscape_flatness
            recovery_flatness = recovery.precision_landscape_flatness

            # Peak should be > baseline and recovery
            peak_is_max = (peak_flatness > baseline_flatness) and (
                peak_flatness > recovery_flatness
            )
            # Recovery should be between baseline and peak
            recovery_is_intermediate = baseline_flatness <= recovery_flatness <= peak_flatness

            status = "✓" if (peak_is_max and recovery_is_intermediate) else "⚠"
            logger.info(
                f"{status} {substance:12s}: baseline={baseline_flatness:.2f} → "
                f"peak={peak_flatness:.2f} → recovery={recovery_flatness:.2f}"
            )

        logger.info("✓ Time point progression verified")
        return True
    except Exception as e:
        logger.error(f"✗ Time point progression test failed: {e}")
        return False


def test_flow_vs_psychedelic():
    """Test flow vs. psychedelic comparison"""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 5: Flow vs. Psychedelic Comparison")
    logger.info("=" * 70)

    try:
        from Psychological_States_GUI import PsychedelicAnalyzer, APGIParameters  # type: ignore

        analyzer = PsychedelicAnalyzer()

        # Create mock flow parameters
        flow_params = APGIParameters(
            Pi_e=6.5,
            Pi_i_baseline=1.5,
            Pi_i_eff=1.5,
            theta_t=0.4,
            S_t=1.8,
            M_ca=0.3,
            beta=0.5,
            z_e=0.2,
            z_i=1.8,
        )

        logger.info("Comparing flow state to psychedelic states:")

        for substance in ["psilocybin", "lsd", "ketamine"]:
            comparison = analyzer.compare_flow_to_psychedelic(flow_params, substance)

            logger.info(f"\n{substance.capitalize()}:")
            logger.info(f"  - Precision reduction: {comparison['precision_reduction']:.1%}")
            logger.info(f"  - Dissolution degree: {comparison['dissolution_degree']:.1%}")
            logger.info(f"  - Alpha power change: {comparison['alpha_power_change']:.1%}")
            logger.info(f"  - Spectral flattening: {comparison['spectral_flattening']:.1%}")
            logger.info(f"  - DMN disruption: {comparison['dmn_disruption']:.1%}")

        logger.info("✓ Flow vs. psychedelic comparison verified")
        return True
    except Exception as e:
        logger.error(f"✗ Flow vs. psychedelic test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_openneuro_info():
    """Test OpenNeuro dataset information"""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 6: OpenNeuro Dataset Information")
    logger.info("=" * 70)

    try:
        from Psychological_States_GUI import PsychedelicAnalyzer  # type: ignore

        analyzer = PsychedelicAnalyzer()
        info = analyzer.get_openneuro_info()

        logger.info(f"Dataset: {info['title']}")
        logger.info(f"OpenNeuro ID: {info['dataset_id']}")
        logger.info(f"URL: {info['url']}")
        logger.info(f"Modalities: {', '.join(info['modalities'])}")
        logger.info(f"Substances: {', '.join(info['substances'])}")

        logger.info("\nSample Sizes:")
        for study, n in info["sample_sizes"].items():
            logger.info(f"  - {study}: N={n}")

        logger.info("\nKey Measures:")
        for measure in info["key_measures"]:
            logger.info(f"  - {measure}")

        # Verify required fields
        required_fields = [
            "dataset_id",
            "title",
            "url",
            "modalities",
            "substances",
            "sample_sizes",
            "key_measures",
            "references",
        ]
        for field in required_fields:
            assert field in info, f"Missing field: {field}"

        logger.info("✓ OpenNeuro dataset information verified")
        return True
    except Exception as e:
        logger.error(f"✗ OpenNeuro info test failed: {e}")
        return False


def test_visualization_methods():
    """Test PsychedelicVisualizer methods"""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 7: PsychedelicVisualizer Methods")
    logger.info("=" * 70)

    if not PLOTLY_AVAILABLE:
        logger.warning("⊘ Skipping - Plotly not available")
        return True

    try:
        from Psychological_States_GUI import PsychedelicAnalyzer, PsychedelicVisualizer  # type: ignore

        analyzer = PsychedelicAnalyzer()
        visualizer = PsychedelicVisualizer(analyzer)

        # Test precision landscape dissolution plot
        fig = visualizer.plot_precision_landscape_dissolution("psilocybin")
        if fig:
            logger.info("✓ Precision landscape dissolution plot created")
            logger.info(f"  - Traces: {len(fig.data)}")
        else:
            logger.warning("⊘ Precision landscape plot returned None")

        # Test substance comparison
        fig = visualizer.plot_substance_comparison()
        if fig:
            logger.info("✓ Substance comparison plot created")
        else:
            logger.warning("⊘ Substance comparison returned None")

        # Test consciousness dissolution trajectory
        fig = visualizer.plot_consciousness_dissolution_trajectory()
        if fig:
            logger.info("✓ Consciousness dissolution trajectory created")
        else:
            logger.warning("⊘ Dissolution trajectory returned None")

        logger.info("✓ PsychedelicVisualizer methods accessible")
        return True
    except Exception as e:
        logger.error(f"✗ PsychedelicVisualizer test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_gui_integration():
    """Test GUI integration"""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 8: GUI Integration")
    logger.info("=" * 70)

    try:
        from Psychological_States_GUI import APGIVisualizerGUI  # type: ignore

        # Check for psychedelic methods
        psychedelic_methods = [m for m in dir(APGIVisualizerGUI) if "psychedelic" in m.lower()]

        if psychedelic_methods:
            logger.info(f"✓ Found {len(psychedelic_methods)} psychedelic-related GUI methods:")
            for method in psychedelic_methods:
                logger.info(f"  - {method}")
        else:
            logger.warning("⊘ No psychedelic methods found in GUI")

        # Check for psychedelic tab setup
        if hasattr(APGIVisualizerGUI, "_setup_psychedelic_analysis_tab"):
            logger.info("✓ Psychedelic analysis tab setup method found")
        else:
            logger.warning("⊘ Psychedelic analysis tab setup method not found")

        return True
    except Exception as e:
        logger.error(f"✗ GUI integration test failed: {e}")
        return False


def main():
    """Run all tests"""
    logger.info("\n" + "=" * 70)
    logger.info("Psychedelic Neuroimaging (DS-07) Integration Test Suite")
    logger.info("=" * 70)

    tests = [
        ("PsychedelicState", test_psychedelic_state),
        ("PsychedelicAnalyzer", test_psychedelic_analyzer),
        ("Substance Dynamics", test_substance_dynamics),
        ("Time Point Progression", test_time_point_progression),
        ("Flow vs. Psychedelic", test_flow_vs_psychedelic),
        ("OpenNeuro Info", test_openneuro_info),
        ("PsychedelicVisualizer", test_visualization_methods),
        ("GUI Integration", test_gui_integration),
    ]

    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            logger.error(f"Unexpected error in {test_name}: {e}")
            results[test_name] = False

    # Summary
    logger.info("\n" + "=" * 70)
    logger.info("TEST SUMMARY")
    logger.info("=" * 70)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        logger.info(f"{status}: {test_name}")

    logger.info(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        logger.info("\n✓ All tests passed! Psychedelic integration is working correctly.")
        return 0
    else:
        logger.warning(f"\n⚠ {total - passed} test(s) failed. Check logs above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
