"""
Tests for Coverage Visualization using naturally updated Fallback classes.
"""

from apgi_framework.gui.coverage_visualization import CoverageData


def test_coverage_data():
    cd = CoverageData()
    assert cd.overall_coverage == 0.0
