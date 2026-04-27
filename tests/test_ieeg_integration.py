#!/usr/bin/env python3
"""
Test suite for DS-09 iEEG Consciousness integration.

Tests the iEEGConsciousnessState, iEEGConsciousnessAnalyzer, and
iEEGConsciousnessVisualizer classes from Psychological-States-GUI.py

Cogitate Consortium (2025): Open multi-center intracranial electroencephalography
dataset with task probing conscious visual perception. Scientific Data.
DOI: 10.1038/s41597-025-04833-z
"""

import sys
import unittest
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import from Psychological-States-GUI
try:
    from Psychological_States_GUI import (
        iEEGConsciousnessAnalyzer,
        iEEGConsciousnessState,
        iEEGConsciousnessVisualizer,
    )

    IMPORTS_AVAILABLE = True
except ImportError:
    IMPORTS_AVAILABLE = False
    print("Warning: Could not import iEEG classes. Some tests will be skipped.")


class TestiEEGConsciousnessState(unittest.TestCase):
    """Test iEEGConsciousnessState dataclass"""

    def setUp(self):
        """Set up test fixtures"""
        if not IMPORTS_AVAILABLE:
            self.skipTest("iEEG classes not available")

        self.state = iEEGConsciousnessState(
            patient_id="P001",
            stimulus_category="face",
            stimulus_duration=1.0,
            stimulus_orientation=0,
            broadband_high_gamma=0.75,
            sustained_activity=0.80,
            ignition_probability=0.85,
            local_recurrence=0.30,
            gnw_prediction=0.82,
            iit_prediction=0.35,
            behavioral_report=True,
            reaction_time=0.45,
            electrode_region="prefrontal_cortex",
        )

    def test_state_creation(self):
        """Test that iEEGConsciousnessState can be created"""
        self.assertEqual(self.state.patient_id, "P001")
        self.assertEqual(self.state.stimulus_category, "face")
        self.assertEqual(self.state.stimulus_duration, 1.0)
        self.assertEqual(self.state.stimulus_orientation, 0)

    def test_consciousness_index(self):
        """Test consciousness_index property"""
        expected = (0.75 + 0.80) / 2.0
        self.assertAlmostEqual(self.state.consciousness_index, expected, places=3)

    def test_gnw_vs_iit_divergence(self):
        """Test gnw_vs_iit_divergence property"""
        expected = 0.82 - 0.35
        self.assertAlmostEqual(self.state.gnw_vs_iit_divergence, expected, places=3)

    def test_ignition_vs_recurrence_ratio(self):
        """Test ignition_vs_recurrence_ratio property"""
        expected = 0.85 / (0.30 + 0.01)
        self.assertAlmostEqual(self.state.ignition_vs_recurrence_ratio, expected, places=3)

    def test_to_dict(self):
        """Test to_dict() method"""
        state_dict = self.state.to_dict()
        self.assertIsInstance(state_dict, dict)
        self.assertEqual(state_dict["patient_id"], "P001")
        self.assertEqual(state_dict["stimulus_category"], "face")
        self.assertIn("consciousness_index", state_dict)
        self.assertIn("gnw_vs_iit_divergence", state_dict)
        self.assertIn("ignition_vs_recurrence_ratio", state_dict)

    def test_state_properties_range(self):
        """Test that state properties are in valid ranges"""
        self.assertGreaterEqual(self.state.consciousness_index, 0.0)
        self.assertLessEqual(self.state.consciousness_index, 1.0)
        self.assertGreaterEqual(self.state.gnw_vs_iit_divergence, -1.0)
        self.assertLessEqual(self.state.gnw_vs_iit_divergence, 1.0)


class TestiEEGConsciousnessAnalyzer(unittest.TestCase):
    """Test iEEGConsciousnessAnalyzer class"""

    def setUp(self):
        """Set up test fixtures"""
        if not IMPORTS_AVAILABLE:
            self.skipTest("iEEG classes not available")

        self.analyzer = iEEGConsciousnessAnalyzer()

    def test_analyzer_initialization(self):
        """Test analyzer initialization"""
        self.assertEqual(self.analyzer.dataset_id, "ds009")
        self.assertEqual(self.analyzer.n_patients, 38)
        self.assertEqual(self.analyzer.n_centers, 3)
        self.assertEqual(len(self.analyzer.stimulus_categories), 4)
        self.assertEqual(len(self.analyzer.stimulus_durations), 3)
        self.assertEqual(len(self.analyzer.stimulus_orientations), 3)

    def test_create_ieeg_state_conscious_face(self):
        """Test creating conscious face stimulus state"""
        state = self.analyzer.create_ieeg_state(
            stimulus_category="face",
            stimulus_duration=1.0,
            stimulus_orientation=0,
            conscious=True,
        )

        self.assertIsInstance(state, iEEGConsciousnessState)
        self.assertEqual(state.stimulus_category, "face")
        self.assertEqual(state.stimulus_duration, 1.0)
        self.assertEqual(state.stimulus_orientation, 0)
        self.assertTrue(state.behavioral_report)

        # Face conscious should have high GNW prediction
        self.assertGreater(state.gnw_prediction, 0.7)
        # Face conscious should have low IIT prediction
        self.assertLess(state.iit_prediction, 0.5)

    def test_create_ieeg_state_unconscious_face(self):
        """Test creating unconscious face stimulus state"""
        state = self.analyzer.create_ieeg_state(
            stimulus_category="face",
            stimulus_duration=1.0,
            stimulus_orientation=0,
            conscious=False,
        )

        self.assertIsInstance(state, iEEGConsciousnessState)
        self.assertFalse(state.behavioral_report)

        # Face unconscious should have low GNW prediction
        self.assertLess(state.gnw_prediction, 0.4)
        # Face unconscious should have high IIT prediction
        self.assertGreater(state.iit_prediction, 0.6)

    def test_create_ieeg_state_all_categories(self):
        """Test creating states for all stimulus categories"""
        for category in self.analyzer.stimulus_categories:
            state = self.analyzer.create_ieeg_state(
                stimulus_category=category,
                stimulus_duration=1.0,
                stimulus_orientation=0,
                conscious=True,
            )
            self.assertEqual(state.stimulus_category, category)
            self.assertIsInstance(state, iEEGConsciousnessState)

    def test_create_ieeg_state_all_durations(self):
        """Test creating states for all stimulus durations"""
        for duration in self.analyzer.stimulus_durations:
            state = self.analyzer.create_ieeg_state(
                stimulus_category="face",
                stimulus_duration=duration,
                stimulus_orientation=0,
                conscious=True,
            )
            self.assertEqual(state.stimulus_duration, duration)

    def test_create_ieeg_state_all_orientations(self):
        """Test creating states for all stimulus orientations"""
        for orientation in self.analyzer.stimulus_orientations:
            state = self.analyzer.create_ieeg_state(
                stimulus_category="face",
                stimulus_duration=1.0,
                stimulus_orientation=orientation,
                conscious=True,
            )
            self.assertEqual(state.stimulus_orientation, orientation)

    def test_duration_modulation(self):
        """Test that stimulus duration modulates consciousness index"""
        states = {}
        for duration in self.analyzer.stimulus_durations:
            state = self.analyzer.create_ieeg_state(
                stimulus_category="face",
                stimulus_duration=duration,
                stimulus_orientation=0,
                conscious=True,
            )
            states[duration] = state.consciousness_index

        # 0.5s should have lower consciousness than 1.0s
        self.assertLess(states[0.5], states[1.0])
        # 1.0s should have lower or equal consciousness than 1.5s
        self.assertLessEqual(states[1.0], states[1.5])

    def test_orientation_modulation(self):
        """Test that stimulus orientation modulates consciousness index"""
        states = {}
        for orientation in self.analyzer.stimulus_orientations:
            state = self.analyzer.create_ieeg_state(
                stimulus_category="face",
                stimulus_duration=1.0,
                stimulus_orientation=orientation,
                conscious=True,
            )
            states[orientation] = state.consciousness_index

        # 0° should have lower or equal consciousness than 90°
        self.assertLessEqual(states[0], states[90])
        # 90° should have lower or equal consciousness than 180°
        self.assertLessEqual(states[90], states[180])

    def test_compare_gnw_vs_iit(self):
        """Test compare_gnw_vs_iit method"""
        comparison = self.analyzer.compare_gnw_vs_iit(
            stimulus_category="face",
            stimulus_duration=1.0,
            stimulus_orientation=0,
        )

        self.assertIsInstance(comparison, dict)
        self.assertIn("gnw_conscious_prediction", comparison)
        self.assertIn("gnw_unconscious_prediction", comparison)
        self.assertIn("iit_conscious_prediction", comparison)
        self.assertIn("iit_unconscious_prediction", comparison)
        self.assertIn("gnw_discrimination", comparison)
        self.assertIn("iit_discrimination", comparison)

        # GNW should discriminate face better than IIT
        self.assertGreater(comparison["gnw_discrimination"], comparison["iit_discrimination"])

    def test_get_cogitate_info(self):
        """Test get_cogitate_info method"""
        info = self.analyzer.get_cogitate_info()

        self.assertIsInstance(info, dict)
        self.assertEqual(info["dataset_id"], "ds009")
        self.assertEqual(info["consortium"], "Cogitate Consortium")
        self.assertEqual(info["n_patients"], 38)
        self.assertEqual(info["n_centers"], 3)
        self.assertIn("title", info)
        self.assertIn("url", info)
        self.assertIn("modalities", info)
        self.assertIn("stimulus_categories", info)
        self.assertIn("key_measures", info)
        self.assertIn("apgi_innovations", info)


class TestiEEGConsciousnessVisualizer(unittest.TestCase):
    """Test iEEGConsciousnessVisualizer class"""

    def setUp(self):
        """Set up test fixtures"""
        if not IMPORTS_AVAILABLE:
            self.skipTest("iEEG classes not available")

        self.analyzer = iEEGConsciousnessAnalyzer()
        self.visualizer = iEEGConsciousnessVisualizer(self.analyzer)

    def test_visualizer_initialization(self):
        """Test visualizer initialization"""
        self.assertIsNotNone(self.visualizer.analyzer)
        self.assertIsNotNone(self.visualizer.renderer)

    def test_plot_gnw_vs_iit_predictions(self):
        """Test plot_gnw_vs_iit_predictions method"""
        fig = self.visualizer.plot_gnw_vs_iit_predictions(
            stimulus_category="face",
            stimulus_duration=1.0,
            stimulus_orientation=0,
        )

        self.assertIsNotNone(fig)
        # Check that figure has data
        self.assertGreater(len(fig.data), 0)

    def test_plot_ignition_vs_recurrence(self):
        """Test plot_ignition_vs_recurrence method"""
        fig = self.visualizer.plot_ignition_vs_recurrence(
            stimulus_category="face",
            stimulus_duration=1.0,
            stimulus_orientation=0,
        )

        self.assertIsNotNone(fig)
        self.assertGreater(len(fig.data), 0)

    def test_plot_stimulus_duration_effects(self):
        """Test plot_stimulus_duration_effects method"""
        fig = self.visualizer.plot_stimulus_duration_effects(
            stimulus_category="face",
            stimulus_orientation=0,
        )

        self.assertIsNotNone(fig)
        self.assertGreater(len(fig.data), 0)

    def test_plot_consciousness_discrimination(self):
        """Test plot_consciousness_discrimination method"""
        fig = self.visualizer.plot_consciousness_discrimination(
            stimulus_category="face",
            stimulus_duration=1.0,
            stimulus_orientation=0,
        )

        self.assertIsNotNone(fig)
        self.assertGreater(len(fig.data), 0)

    def test_all_visualization_types(self):
        """Test all visualization types generate without errors"""
        viz_types = [
            "gnw_vs_iit",
            "ignition_vs_recurrence",
            "duration_effects",
            "discrimination",
        ]

        for viz_type in viz_types:
            if viz_type == "gnw_vs_iit":
                fig = self.visualizer.plot_gnw_vs_iit_predictions("face", 1.0, 0)
            elif viz_type == "ignition_vs_recurrence":
                fig = self.visualizer.plot_ignition_vs_recurrence("face", 1.0, 0)
            elif viz_type == "duration_effects":
                fig = self.visualizer.plot_stimulus_duration_effects("face", 0)
            elif viz_type == "discrimination":
                fig = self.visualizer.plot_consciousness_discrimination("face", 1.0, 0)

            self.assertIsNotNone(fig, f"Failed to generate {viz_type} visualization")


class TestiEEGIntegration(unittest.TestCase):
    """Integration tests for iEEG consciousness analysis"""

    def setUp(self):
        """Set up test fixtures"""
        if not IMPORTS_AVAILABLE:
            self.skipTest("iEEG classes not available")

        self.analyzer = iEEGConsciousnessAnalyzer()
        self.visualizer = iEEGConsciousnessVisualizer(self.analyzer)

    def test_gnw_advantage_for_faces(self):
        """Test that GNW has advantage for face stimuli (I-20 prediction)"""
        comparison = self.analyzer.compare_gnw_vs_iit(
            stimulus_category="face",
            stimulus_duration=1.0,
            stimulus_orientation=0,
        )

        # GNW should discriminate faces better than IIT
        gnw_disc = comparison["gnw_discrimination"]
        iit_disc = comparison["iit_discrimination"]

        self.assertGreater(gnw_disc, 0.4, "GNW should have strong discrimination for faces")
        self.assertLess(iit_disc, 0.0, "IIT should have weak/negative discrimination for faces")

    def test_iit_advantage_for_scrambled(self):
        """Test that IIT has advantage for scrambled stimuli"""
        comparison = self.analyzer.compare_gnw_vs_iit(
            stimulus_category="scrambled",
            stimulus_duration=1.0,
            stimulus_orientation=0,
        )

        # IIT should discriminate scrambled better than GNW
        gnw_disc = comparison["gnw_discrimination"]
        iit_disc = comparison["iit_discrimination"]

        self.assertLess(gnw_disc, 0.1, "GNW should have weak discrimination for scrambled")
        self.assertGreater(iit_disc, 0.0, "IIT should have better discrimination for scrambled")

    def test_sustained_ignition_threshold(self):
        """Test sustained ignition threshold at 1.0s (I-20 prediction)"""
        states = {}
        for duration in self.analyzer.stimulus_durations:
            state = self.analyzer.create_ieeg_state(
                stimulus_category="face",
                stimulus_duration=duration,
                stimulus_orientation=0,
                conscious=True,
            )
            states[duration] = state

        # Consciousness should increase with duration (sustained ignition)
        self.assertLess(
            states[0.5].consciousness_index,
            states[1.0].consciousness_index,
            "Consciousness should increase from 0.5s to 1.0s",
        )

        self.assertLessEqual(
            states[1.0].consciousness_index,
            states[1.5].consciousness_index,
            "Consciousness should maintain or increase from 1.0s to 1.5s",
        )

    def test_ignition_recurrence_dissociation(self):
        """Test dissociation between ignition and recurrence (I-33 prediction)"""
        conscious_state = self.analyzer.create_ieeg_state(
            stimulus_category="face",
            stimulus_duration=1.0,
            stimulus_orientation=0,
            conscious=True,
        )

        unconscious_state = self.analyzer.create_ieeg_state(
            stimulus_category="face",
            stimulus_duration=1.0,
            stimulus_orientation=0,
            conscious=False,
        )

        # Conscious should have high ignition, low recurrence
        self.assertGreater(
            conscious_state.ignition_probability,
            conscious_state.local_recurrence,
            "Conscious state should have ignition > recurrence",
        )

        # Unconscious should have low ignition, high recurrence
        self.assertLess(
            unconscious_state.ignition_probability,
            unconscious_state.local_recurrence,
            "Unconscious state should have ignition < recurrence",
        )

    def test_consciousness_discrimination_across_categories(self):
        """Test consciousness discrimination across all stimulus categories"""
        for category in self.analyzer.stimulus_categories:
            comparison = self.analyzer.compare_gnw_vs_iit(
                stimulus_category=category,
                stimulus_duration=1.0,
                stimulus_orientation=0,
            )

            # All categories should show some discrimination
            gnw_disc = comparison["gnw_discrimination"]
            iit_disc = comparison["iit_discrimination"]

            # At least one model should discriminate
            self.assertTrue(
                abs(gnw_disc) > 0.1 or abs(iit_disc) > 0.1,
                f"No discrimination for {category}",
            )


def run_tests():
    """Run all tests"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestiEEGConsciousnessState))
    suite.addTests(loader.loadTestsFromTestCase(TestiEEGConsciousnessAnalyzer))
    suite.addTests(loader.loadTestsFromTestCase(TestiEEGConsciousnessVisualizer))
    suite.addTests(loader.loadTestsFromTestCase(TestiEEGIntegration))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Return exit code
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(run_tests())
