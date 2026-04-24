"""
Tests for various module imports to ensure coverage of __init__.py files.
"""


def test_adaptive_imports() -> None:
    """Test imports from apgi_framework.adaptive."""
    import apgi_framework.adaptive as adaptive

    assert hasattr(adaptive, "__name__")


def test_analysis_imports() -> None:
    """Test imports from apgi_framework.analysis."""
    import apgi_framework.analysis as analysis

    assert hasattr(analysis, "__name__")


def test_clinical_imports() -> None:
    """Test imports from apgi_framework.clinical."""
    import apgi_framework.clinical as clinical

    assert hasattr(clinical, "__name__")


def test_data_imports() -> None:
    """Test imports from apgi_framework.data."""
    import apgi_framework.data as data

    assert hasattr(data, "__name__")


def test_deployment_imports() -> None:
    """Test imports from apgi_framework.deployment."""
    import apgi_framework.deployment as deployment

    assert hasattr(deployment, "__name__")


def test_export_imports() -> None:
    """Test imports from apgi_framework.export."""
    import apgi_framework.export as export

    assert hasattr(export, "__name__")


def test_gui_imports() -> None:
    """Test imports from apgi_framework.gui."""
    import apgi_framework.gui as gui

    assert hasattr(gui, "__name__")


def test_gui_components_imports() -> None:
    """Test imports from apgi_framework.gui.components."""
    import apgi_framework.gui.components as components

    assert hasattr(components, "__name__")


def test_neural_imports() -> None:
    """Test imports from apgi_framework.neural."""
    import apgi_framework.neural as neural

    assert hasattr(neural, "__name__")


def test_security_imports() -> None:
    """Test imports from apgi_framework.security."""
    import apgi_framework.security as security

    assert hasattr(security, "__name__")


def test_simulators_imports() -> None:
    """Test imports from apgi_framework.simulators."""
    import apgi_framework.simulators as simulators

    assert hasattr(simulators, "__name__")
    assert hasattr(simulators, "P3bSimulator")


def test_testing_package_imports() -> None:
    """Test imports from apgi_framework.testing."""
    import apgi_framework.testing as testing

    assert hasattr(testing, "__name__")


def test_utils_imports() -> None:
    """Test imports from apgi_framework.utils."""
    import apgi_framework.utils as utils

    assert hasattr(utils, "__name__")


def test_validation_package_imports() -> None:
    """Test imports from apgi_framework.validation."""
    import apgi_framework.validation as validation

    assert hasattr(validation, "__name__")
