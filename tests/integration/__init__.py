"""
Integration Tests Package

This package contains comprehensive integration tests for the APGI Framework
Test Enhancement System, including end-to-end workflow tests, APGI framework
compatibility tests, and property-based integration tests.

Test Modules:
- test_end_to_end_workflow.py: Complete workflow tests from discovery to reporting
- test_apgi_framework_compatibility.py: APGI framework integration and synthetic data tests
- test_integration_properties.py: Property-based tests for integration scenarios

Requirements Coverage:
- 7.1: Test fixture compatibility with existing APGI components
- 7.2: Synthetic data generation for neural signal processing
- All integration requirements: Component interaction and data flow validation
"""

__version__ = "1.0.0"
__author__ = "APGI Framework Test Enhancement Team"

# Note: Do not import from test modules in __init__.py to avoid circular import issues
# during pytest collection. Test classes are available through direct imports.
