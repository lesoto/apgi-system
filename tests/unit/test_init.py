"""
Unit tests for apgi_system package initialization.

This module tests that the package can be imported and that
all expected classes are available from the package level.
"""


def test_package_imports() -> None:
    """Test that main classes can be imported from apgi_system package."""
    from apgi_system import (
        ActiveInferenceEngine,
        FreeEnergyCalculator,
        HierarchicalPredictor,
        PrecisionWeighting,
    )

    # Verify classes are imported correctly
    assert ActiveInferenceEngine is not None
    assert FreeEnergyCalculator is not None
    assert HierarchicalPredictor is not None
    assert PrecisionWeighting is not None


def test_package_version() -> None:
    """Test that package version is defined."""
    import apgi_system

    assert hasattr(apgi_system, "__version__")
    assert isinstance(apgi_system.__version__, str)
    assert len(apgi_system.__version__) > 0


def test_package_all() -> None:
    """Test that __all__ is properly defined."""
    import apgi_system

    assert hasattr(apgi_system, "__all__")
    assert isinstance(apgi_system.__all__, list)
    assert len(apgi_system.__all__) == 4
    expected = [
        "ActiveInferenceEngine",
        "FreeEnergyCalculator",
        "HierarchicalPredictor",
        "PrecisionWeighting",
    ]
    assert apgi_system.__all__ == expected
