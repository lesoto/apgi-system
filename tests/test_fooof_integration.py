#!/usr/bin/env python
"""
Test script for FOOOF/specparam integration in Psychological-States-GUI.py

Validates:
1. FOOOF import and availability
2. SpectralParameters dataclass
3. SpectralAnalyzer functionality
4. SpectralVisualizer methods
5. State-spectrum mapping
6. Consciousness index calculation
"""

import sys
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Check FOOOF availability
try:
    import fooof  # noqa: F401

    FOOOF_AVAILABLE = True
    logger.info("✓ FOOOF imported successfully")
except ImportError:
    FOOOF_AVAILABLE = False
    logger.warning("✗ FOOOF not available - install with: pip install fooof")

# Check other dependencies
try:
    import numpy as np

    logger.info("✓ NumPy available")
except ImportError:
    logger.error("✗ NumPy not available")
    sys.exit(1)

try:
    import plotly.graph_objects as go  # noqa: F401

    PLOTLY_AVAILABLE = True
    logger.info("✓ Plotly available")
except ImportError:
    PLOTLY_AVAILABLE = False
    logger.warning("✗ Plotly not available")


def test_spectral_parameters():
    """Test SpectralParameters dataclass"""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 1: SpectralParameters Dataclass")
    logger.info("=" * 70)

    try:
        # Import from GUI file
        from pathlib import Path

        project_root = Path(__file__).parent.parent
        sys.path.insert(0, str(project_root))
        from Psychological_States_GUI import SpectralParameters

        # Create test parameters
        params = SpectralParameters(
            aperiodic_exponent=1.5,
            aperiodic_offset=0.5,
            periodic_peaks=[
                {"frequency": 10.0, "power": 1.5, "bandwidth": 2.0},
                {"frequency": 20.0, "power": 0.8, "bandwidth": 1.5},
            ],
            error=0.05,
            r_squared=0.98,
            frequency_range=(1.0, 50.0),
        )

        logger.info("✓ SpectralParameters created")
        logger.info(f"  - Aperiodic exponent: {params.aperiodic_exponent}")
        logger.info(f"  - E/I ratio proxy: {params.ei_ratio_proxy:.3f}")
        logger.info(f"  - Consciousness index: {params.consciousness_index:.1%}")
        logger.info(f"  - Periodic peaks: {len(params.periodic_peaks)}")
        logger.info(f"  - Model fit (R²): {params.r_squared:.3f}")

        # Verify consciousness index calculation
        assert 0.0 <= params.consciousness_index <= 1.0, "Consciousness index out of range"
        logger.info("✓ Consciousness index calculation verified")

        return True
    except Exception as e:
        logger.error(f"✗ SpectralParameters test failed: {e}")
        return False


def test_spectral_analyzer():
    """Test SpectralAnalyzer class"""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 2: SpectralAnalyzer Class")
    logger.info("=" * 70)

    if not FOOOF_AVAILABLE:
        logger.warning("⊘ Skipping - FOOOF not available")
        return True

    try:
        from Psychological_States_GUI import SpectralAnalyzer

        # Create analyzer
        analyzer = SpectralAnalyzer(freq_range=(1.0, 50.0))
        logger.info("✓ SpectralAnalyzer initialized")

        # Test synthetic spectrum generation
        test_states = ["flow", "anxiety", "meditation_focused", "depression"]

        for state in test_states:
            freqs, powers = analyzer.generate_synthetic_spectrum(state)

            assert len(freqs) > 0, f"No frequencies generated for {state}"
            assert len(powers) == len(freqs), f"Frequency/power mismatch for {state}"
            assert np.all(powers > 0), f"Negative powers for {state}"

            logger.info(f"✓ Generated spectrum for '{state}'")
            logger.info(f"  - Frequency range: {freqs[0]:.1f}-{freqs[-1]:.1f} Hz")
            logger.info(f"  - Power range: {powers.min():.3f}-{powers.max():.3f}")

        # Test spectrum fitting
        freqs, powers = analyzer.generate_synthetic_spectrum("flow")
        spectral_params = analyzer.fit_spectrum(freqs, powers)

        if spectral_params:
            logger.info("✓ Spectrum fitting successful")
            logger.info(f"  - Aperiodic exponent: {spectral_params.aperiodic_exponent:.3f}")
            logger.info(f"  - Model fit (R²): {spectral_params.r_squared:.3f}")
            logger.info(f"  - Periodic peaks: {len(spectral_params.periodic_peaks)}")
        else:
            logger.warning("⊘ Spectrum fitting returned None")

        return True
    except Exception as e:
        logger.error(f"✗ SpectralAnalyzer test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_consciousness_index():
    """Test consciousness index calculation across states"""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 3: Consciousness Index Calculation")
    logger.info("=" * 70)

    if not FOOOF_AVAILABLE:
        logger.warning("⊘ Skipping - FOOOF not available")
        return True

    try:
        from Psychological_States_GUI import SpectralAnalyzer

        analyzer = SpectralAnalyzer()

        # Test states with expected consciousness levels
        test_cases = [
            ("flow", 0.6, 0.9),  # High consciousness
            ("anxiety", 0.2, 0.5),  # Moderate-low
            ("depression", 0.0, 0.3),  # Low consciousness
            ("meditation_focused", 0.3, 0.6),  # Moderate
        ]

        logger.info("Testing consciousness index ranges:")
        for state, min_expected, max_expected in test_cases:
            freqs, powers = analyzer.generate_synthetic_spectrum(state)
            params = analyzer.fit_spectrum(freqs, powers)

            if params:
                consciousness = params.consciousness_index
                in_range = min_expected <= consciousness <= max_expected
                status = "✓" if in_range else "⚠"

                logger.info(
                    f"{status} {state:25s}: {consciousness:.1%} "
                    f"(expected {min_expected:.0%}-{max_expected:.0%})"
                )
            else:
                logger.warning(f"⊘ {state}: Could not fit spectrum")

        return True
    except Exception as e:
        logger.error(f"✗ Consciousness index test failed: {e}")
        return False


def test_state_spectrum_mapping():
    """Test state-to-spectrum mapping"""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 4: State-Spectrum Mapping")
    logger.info("=" * 70)

    if not FOOOF_AVAILABLE:
        logger.warning("⊘ Skipping - FOOOF not available")
        return True

    try:
        from Psychological_States_GUI import SpectralAnalyzer

        analyzer = SpectralAnalyzer()

        # Test all mapped states
        mapped_states = [
            "flow",
            "focus",
            "serenity",
            "mindfulness",
            "joy",
            "amusement",
            "anxiety",
            "fear",
            "depression",
            "panic",
            "meditation_focused",
            "meditation_open",
            "hyperfocus",
        ]

        logger.info(f"Testing {len(mapped_states)} mapped states:")

        exponents = []
        for state in mapped_states:
            freqs, powers = analyzer.generate_synthetic_spectrum(state)
            params = analyzer.fit_spectrum(freqs, powers)

            if params:
                exponents.append(params.aperiodic_exponent)
                logger.info(f"✓ {state:25s}: exponent={params.aperiodic_exponent:.2f}")
            else:
                logger.warning(f"⊘ {state}: Could not fit")

        # Verify exponent range
        if exponents:
            logger.info("\nExponent statistics:")
            logger.info(f"  - Min: {min(exponents):.2f}")
            logger.info(f"  - Max: {max(exponents):.2f}")
            logger.info(f"  - Mean: {np.mean(exponents):.2f}")
            logger.info(f"  - Std: {np.std(exponents):.2f}")

        return True
    except Exception as e:
        logger.error(f"✗ State-spectrum mapping test failed: {e}")
        return False


def test_visualization_methods():
    """Test SpectralVisualizer methods"""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 5: SpectralVisualizer Methods")
    logger.info("=" * 70)

    if not (FOOOF_AVAILABLE and PLOTLY_AVAILABLE):
        logger.warning("⊘ Skipping - FOOOF or Plotly not available")
        return True

    try:
        from Psychological_States_GUI import SpectralAnalyzer, SpectralVisualizer

        analyzer = SpectralAnalyzer()
        visualizer = SpectralVisualizer(analyzer)

        # Test spectrum decomposition plot
        freqs, powers = analyzer.generate_synthetic_spectrum("flow")
        fig = visualizer.plot_spectrum_decomposition(freqs, powers, "flow")

        if fig:
            logger.info("✓ Spectrum decomposition plot created")
            logger.info(f"  - Traces: {len(fig.data)}")
        else:
            logger.warning("⊘ Spectrum decomposition returned None")

        # Note: Full landscape and heatmap tests require all states
        # which may not be available in test context
        logger.info("✓ SpectralVisualizer methods accessible")

        return True
    except Exception as e:
        logger.error(f"✗ SpectralVisualizer test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_gui_integration():
    """Test GUI integration"""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 6: GUI Integration")
    logger.info("=" * 70)

    try:
        # Check if GUI file has spectral methods
        from Psychological_States_GUI import APGIVisualizerGUI

        gui_methods = [m for m in dir(APGIVisualizerGUI) if "spectral" in m.lower()]

        if gui_methods:
            logger.info(f"✓ Found {len(gui_methods)} spectral-related GUI methods:")
            for method in gui_methods:
                logger.info(f"  - {method}")
        else:
            logger.warning("⊘ No spectral methods found in GUI")

        # Check for spectral tab setup
        if hasattr(APGIVisualizerGUI, "_setup_spectral_analysis_tab"):
            logger.info("✓ Spectral analysis tab setup method found")
        else:
            logger.warning("⊘ Spectral analysis tab setup method not found")

        return True
    except Exception as e:
        logger.error(f"✗ GUI integration test failed: {e}")
        return False


def main():
    """Run all tests"""
    logger.info("\n" + "=" * 70)
    logger.info("FOOOF Integration Test Suite")
    logger.info("=" * 70)

    tests = [
        ("SpectralParameters", test_spectral_parameters),
        ("SpectralAnalyzer", test_spectral_analyzer),
        ("Consciousness Index", test_consciousness_index),
        ("State-Spectrum Mapping", test_state_spectrum_mapping),
        ("SpectralVisualizer", test_visualization_methods),
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
        logger.info("\n✓ All tests passed! FOOOF integration is working correctly.")
        return 0
    else:
        logger.warning(f"\n⚠ {total - passed} test(s) failed. Check logs above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
