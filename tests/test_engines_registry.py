"""
Tests for the Engine Registry module.

This module contains comprehensive tests for the EngineRegistry,
ensuring proper engine registration, instantiation, and lifecycle management.
"""

import pytest

from apgi_framework.engines import (
    EngineRegistry,
    EngineMetadata,
    EngineType,
    SomaticMarkerEngine,
    ThresholdManager,
    APGIEquation,
    PrecisionCalculator,
    PredictionErrorProcessor,
    PredictiveIgnitionNetwork,
)


class TestEngineType:
    """Tests for EngineType enum."""

    def test_engine_type_values(self):
        """Test that all engine types are defined."""
        assert EngineType.SOMATIC_MARKER is not None
        assert EngineType.THRESHOLD is not None
        assert EngineType.EQUATION is not None
        assert EngineType.PRECISION is not None
        assert EngineType.PREDICTION_ERROR is not None
        assert EngineType.PREDICTIVE_IGNITION is not None
        assert EngineType.SIMULATION is not None
        assert EngineType.SIMULATION is not None


class TestEngineMetadata:
    """Tests for EngineMetadata class."""

    def test_metadata_creation(self):
        """Test creating engine metadata."""
        metadata = EngineMetadata(
            name="test_engine",
            engine_type=EngineType.SOMATIC_MARKER,
            engine_class=SomaticMarkerEngine,
            description="Test engine description",
            version="1.0.0",
            dependencies=["numpy"],
            config_schema={"param": "value"},
        )

        assert metadata.name == "test_engine"
        assert metadata.engine_type == EngineType.SOMATIC_MARKER
        assert metadata.engine_class == SomaticMarkerEngine
        assert metadata.description == "Test engine description"
        assert metadata.version == "1.0.0"
        assert metadata.dependencies == ["numpy"]
        assert metadata.config_schema == {"param": "value"}

    def test_metadata_defaults(self):
        """Test metadata with default values."""
        metadata = EngineMetadata(
            name="default_engine",
            engine_type=EngineType.THRESHOLD,
            engine_class=ThresholdManager,
            description="Default test engine",
        )

        assert metadata.version == "1.0.0"
        assert metadata.dependencies == []
        assert metadata.config_schema == {}


class TestEngineRegistry:
    """Tests for EngineRegistry class."""

    @pytest.fixture(autouse=True)
    def reset_registry(self):
        """Reset registry singleton before each test."""
        EngineRegistry._instance = None
        EngineRegistry._engines = {}
        EngineRegistry._instances = {}
        yield
        # Cleanup after test
        if EngineRegistry._instance:
            EngineRegistry._instance.clear_instances()
        EngineRegistry._instance = None

    def test_singleton_pattern(self):
        """Test that registry is a singleton."""
        registry1 = EngineRegistry()
        registry2 = EngineRegistry()
        assert registry1 is registry2

    def test_default_engines_registered(self):
        """Test that default engines are registered on initialization."""
        registry = EngineRegistry()

        assert registry.is_registered("somatic_marker")
        assert registry.is_registered("threshold")
        assert registry.is_registered("equation")
        assert registry.is_registered("precision")
        assert registry.is_registered("prediction_error")
        assert registry.is_registered("predictive_ignition")

    def test_register_engine(self):
        """Test registering a custom engine."""
        registry = EngineRegistry()

        metadata = EngineMetadata(
            name="custom_engine",
            engine_type=EngineType.SIMULATION,
            engine_class=APGIEquation,
            description="Custom test engine",
        )

        registry.register(metadata)
        assert registry.is_registered("custom_engine")

    def test_register_duplicate_engine_raises_error(self):
        """Test that registering duplicate engine raises ValueError."""
        registry = EngineRegistry()

        metadata = EngineMetadata(
            name="custom_engine",
            engine_type=EngineType.SIMULATION,
            engine_class=APGIEquation,
            description="Custom test engine",
        )

        registry.register(metadata)

        with pytest.raises(ValueError, match="already registered"):
            registry.register(metadata)

    def test_unregister_engine(self):
        """Test unregistering an engine."""
        registry = EngineRegistry()

        metadata = EngineMetadata(
            name="temp_engine",
            engine_type=EngineType.SIMULATION,
            engine_class=APGIEquation,
            description="Temporary engine",
        )

        registry.register(metadata)
        assert registry.is_registered("temp_engine")

        registry.unregister("temp_engine")
        assert not registry.is_registered("temp_engine")

    def test_get_engine(self):
        """Test getting engine metadata."""
        registry = EngineRegistry()

        metadata = registry.get_engine("somatic_marker")
        assert metadata is not None
        assert metadata.name == "somatic_marker"
        assert metadata.engine_type == EngineType.SOMATIC_MARKER

    def test_get_nonexistent_engine(self):
        """Test getting non-existent engine returns None."""
        registry = EngineRegistry()
        assert registry.get_engine("nonexistent") is None

    def test_list_engines(self):
        """Test listing all engines."""
        registry = EngineRegistry()
        engines = registry.list_engines()

        assert "somatic_marker" in engines
        assert "threshold" in engines
        assert "equation" in engines

    def test_list_engines_by_type(self):
        """Test filtering engines by type."""
        registry = EngineRegistry()
        somatic_engines = registry.list_engines(EngineType.SOMATIC_MARKER)

        assert "somatic_marker" in somatic_engines
        assert "threshold" not in somatic_engines

    def test_get_engines_by_type(self):
        """Test getting engines by type as dictionary."""
        registry = EngineRegistry()
        engines = registry.get_engines_by_type(EngineType.SOMATIC_MARKER)

        assert "somatic_marker" in engines
        assert engines["somatic_marker"].engine_type == EngineType.SOMATIC_MARKER

    def test_create_engine_somatic_marker(self):
        """Test creating somatic marker engine instance."""
        registry = EngineRegistry()
        engine = registry.create_engine("somatic_marker")

        assert isinstance(engine, SomaticMarkerEngine)

    def test_create_engine_threshold(self):
        """Test creating threshold manager engine instance."""
        registry = EngineRegistry()
        engine = registry.create_engine("threshold")

        assert isinstance(engine, ThresholdManager)

    def test_create_engine_equation(self):
        """Test creating equation engine instance."""
        registry = EngineRegistry()
        engine = registry.create_engine("equation")

        assert isinstance(engine, APGIEquation)

    def test_create_engine_precision(self):
        """Test creating precision calculator engine instance."""
        registry = EngineRegistry()
        engine = registry.create_engine("precision")

        assert isinstance(engine, PrecisionCalculator)

    def test_create_engine_prediction_error(self):
        """Test creating prediction error processor engine instance."""
        registry = EngineRegistry()
        engine = registry.create_engine("prediction_error")

        assert isinstance(engine, PredictionErrorProcessor)

    def test_create_engine_predictive_ignition(self):
        """Test creating predictive ignition network engine instance."""
        registry = EngineRegistry()
        engine = registry.create_engine("predictive_ignition")

        assert isinstance(engine, PredictiveIgnitionNetwork)

    def test_create_nonexistent_engine_raises_error(self):
        """Test creating non-existent engine raises ValueError."""
        registry = EngineRegistry()

        with pytest.raises(ValueError, match="not found"):
            registry.create_engine("nonexistent_engine")

    def test_create_engine_singleton(self):
        """Test that singleton pattern returns same instance."""
        registry = EngineRegistry()
        engine1 = registry.create_engine("somatic_marker")
        engine2 = registry.create_engine("somatic_marker")

        assert engine1 is engine2

    def test_create_engine_non_singleton(self):
        """Test that non-singleton creates new instances."""
        registry = EngineRegistry()
        engine1 = registry.create_engine("somatic_marker", singleton=False)
        engine2 = registry.create_engine("somatic_marker", singleton=False)

        assert engine1 is not engine2

    def test_create_engine_with_config(self):
        """Test creating engine with configuration."""
        registry = EngineRegistry()

        # Test with empty config (most engines work with defaults)
        engine = registry.create_engine("somatic_marker", config={}, singleton=False)

        assert isinstance(engine, SomaticMarkerEngine)

    def test_dispose_engine(self):
        """Test disposing of engine instance."""
        registry = EngineRegistry()
        registry.create_engine("somatic_marker")
        registry.dispose_engine("somatic_marker")
        # Should not raise error

    def test_clear_instances(self):
        """Test clearing all engine instances."""
        registry = EngineRegistry()
        registry.create_engine("somatic_marker")
        registry.create_engine("threshold")

        registry.clear_instances()

        # After clearing, should create new instances
        engine = registry.create_engine("somatic_marker", singleton=False)
        assert isinstance(engine, SomaticMarkerEngine)

    def test_get_engine_info(self):
        """Test getting engine information dictionary."""
        registry = EngineRegistry()
        info = registry.get_engine_info()

        assert "somatic_marker" in info
        assert "type" in info["somatic_marker"]
        assert "description" in info["somatic_marker"]
        assert "version" in info["somatic_marker"]
        assert "dependencies" in info["somatic_marker"]
        assert "class" in info["somatic_marker"]


class TestEngineRegistryIntegration:
    """Integration tests for EngineRegistry."""

    @pytest.fixture(autouse=True)
    def reset_registry(self):
        """Reset registry singleton before each test."""
        EngineRegistry._instance = None
        EngineRegistry._engines = {}
        EngineRegistry._instances = {}
        yield
        if EngineRegistry._instance:
            EngineRegistry._instance.clear_instances()
        EngineRegistry._instance = None

    def test_full_lifecycle(self):
        """Test complete engine lifecycle."""
        registry = EngineRegistry()

        # Register custom engine
        metadata = EngineMetadata(
            name="lifecycle_test",
            engine_type=EngineType.SIMULATION,
            engine_class=SomaticMarkerEngine,
            description="Lifecycle test engine",
        )
        registry.register(metadata)

        # Create instance
        engine = registry.create_engine("lifecycle_test")
        assert isinstance(engine, SomaticMarkerEngine)

        # Verify registration
        assert registry.is_registered("lifecycle_test")

        # Dispose
        registry.dispose_engine("lifecycle_test")

        # Unregister
        registry.unregister("lifecycle_test")
        assert not registry.is_registered("lifecycle_test")

    def test_multiple_engine_types(self):
        """Test handling multiple engine types simultaneously."""
        registry = EngineRegistry()

        # Get all engines by type
        core_engines = registry.get_engines_by_type(EngineType.EQUATION)
        somatic_engines = registry.get_engines_by_type(EngineType.SOMATIC_MARKER)

        # Verify type separation
        for name in core_engines:
            assert core_engines[name].engine_type == EngineType.EQUATION
        for name in somatic_engines:
            assert somatic_engines[name].engine_type == EngineType.SOMATIC_MARKER

    def test_engine_list_comprehensive(self):
        """Test comprehensive engine listing."""
        registry = EngineRegistry()

        all_engines = registry.list_engines()
        somatic_engines = registry.list_engines(EngineType.SOMATIC_MARKER)
        threshold_engines = registry.list_engines(EngineType.THRESHOLD)

        # Verify all engines are accounted for
        assert len(all_engines) >= 6  # At least default engines
        assert len(somatic_engines) >= 1
        assert len(threshold_engines) >= 1

        # Verify no overlap between different types
        assert not set(somatic_engines) & set(threshold_engines)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
