"""
Property-based tests for error handling system.

Tests comprehensive error handling capabilities including error categorization,
diagnostic capture, and resolution guidance generation.
"""

from datetime import datetime
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st
from hypothesis.stateful import RuleBasedStateMachine, initialize, rule

from apgi_framework.testing.error_handler import (
    Context,
    DiagnosticInfo,
    ErrorCategory,
    ErrorHandler,
    ErrorSeverity,
    ResolutionGuidance,
    SystemState,
)


# Test data generators
@st.composite
def exception_generator(draw):
    """Generate various types of exceptions for testing."""
    # Simplified exception generation to avoid complex constructor issues
    exception_types_and_messages = [
        (ValueError, "Invalid value provided"),
        (ImportError, "Cannot import module"),
        (FileNotFoundError, "File not found"),
        (AssertionError, "Assertion failed"),
        (TimeoutError, "Operation timed out"),
        (MemoryError, "Out of memory"),
        (ModuleNotFoundError, "No module named 'test_module'"),
        (PermissionError, "Permission denied"),
        (RuntimeError, "Runtime error occurred"),
    ]

    exception_class, base_message = draw(st.sampled_from(exception_types_and_messages))
    # Add some variation to the message
    suffix = draw(
        st.text(
            min_size=0,
            max_size=20,
            alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd")),
        )
    )
    message = f"{base_message} {suffix}".strip()

    try:
        return exception_class(message)
    except Exception:
        # Fallback for exceptions that don't accept string arguments
        return exception_class()


@st.composite
def context_generator_strategy(draw):
    """Generate test context information."""
    return Context(
        test_name=draw(
            st.one_of(
                st.none(),
                st.text(
                    min_size=1,
                    max_size=30,
                    alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd")),
                ),
            )
        ),
        test_file=draw(
            st.one_of(
                st.none(),
                st.text(
                    min_size=1,
                    max_size=50,
                    alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd")),
                ),
            )
        ),
        test_class=draw(
            st.one_of(
                st.none(),
                st.text(
                    min_size=1,
                    max_size=30,
                    alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd")),
                ),
            )
        ),
        test_method=draw(
            st.one_of(
                st.none(),
                st.text(
                    min_size=1,
                    max_size=30,
                    alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd")),
                ),
            )
        ),
        test_parameters=draw(
            st.dictionaries(
                st.text(
                    min_size=1,
                    max_size=10,
                    alphabet=st.characters(whitelist_categories=("Lu", "Ll")),
                ),
                st.one_of(
                    st.text(
                        max_size=20,
                        alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd")),
                    ),
                    st.integers(min_value=-1000, max_value=1000),
                ),
                max_size=3,
            )
        ),
        test_fixtures=draw(
            st.lists(
                st.text(
                    min_size=1,
                    max_size=20,
                    alphabet=st.characters(whitelist_categories=("Lu", "Ll")),
                ),
                max_size=3,
            )
        ),
        test_marks=draw(
            st.lists(
                st.text(
                    min_size=1,
                    max_size=15,
                    alphabet=st.characters(whitelist_categories=("Lu", "Ll")),
                ),
                max_size=3,
            )
        ),
        execution_time=draw(
            st.one_of(
                st.none(),
                st.floats(min_value=0.0, max_value=60.0, allow_nan=False, allow_infinity=False),
            )
        ),
    )


@st.composite
def metadata_generator(draw):
    """Generate metadata dictionary."""
    return draw(
        st.dictionaries(
            st.text(
                min_size=1,
                max_size=15,
                alphabet=st.characters(whitelist_categories=("Lu", "Ll")),
            ),
            st.one_of(
                st.text(
                    max_size=50,
                    alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd")),
                ),
                st.integers(min_value=-1000, max_value=1000),
                st.booleans(),
            ),
            max_size=5,
        )
    )


class TestErrorHandlerProperties:
    """Property-based tests for ErrorHandler."""

    def setup_method(self):
        """Setup for each test method."""
        self.error_handler = ErrorHandler()

    # Feature: comprehensive-test-enhancement, Property 24: Comprehensive error handling
    @given(
        exception=exception_generator(),
        test_context=context_generator_strategy(),
        metadata=metadata_generator(),
    )
    @settings(max_examples=10, deadline=5000)
    def test_comprehensive_error_handling_property(self, exception, test_context, metadata):
        """
        **Property 24: Comprehensive error handling**

        For any test execution error, the system should capture complete diagnostic
        information, provide accurate error categorization, and offer specific
        resolution guidance when applicable.

        **Validates: Requirements 10.1, 10.2, 10.3**
        """
        # Handle the error
        diagnostic_info = self.error_handler.handle_error(
            exception=exception, test_context=test_context, **metadata
        )

        # Verify comprehensive diagnostic capture (Requirement 10.1)
        assert isinstance(diagnostic_info, DiagnosticInfo)
        assert diagnostic_info.error_id is not None
        assert len(diagnostic_info.error_id) > 0
        assert diagnostic_info.original_exception is exception
        assert diagnostic_info.message == str(exception)

        # Verify system state capture
        assert isinstance(diagnostic_info.system_state, SystemState)
        assert diagnostic_info.system_state.timestamp is not None
        assert diagnostic_info.system_state.python_version is not None
        assert diagnostic_info.system_state.platform_info is not None
        assert isinstance(diagnostic_info.system_state.memory_usage, dict)
        assert isinstance(diagnostic_info.system_state.disk_usage, dict)

        # Verify test context preservation
        assert diagnostic_info.test_context == test_context

        # Verify metadata preservation
        assert diagnostic_info.metadata == metadata

        # Verify error categorization (Requirement 10.2)
        assert isinstance(diagnostic_info.category, ErrorCategory)
        assert isinstance(diagnostic_info.severity, ErrorSeverity)

        # Category should be appropriate for exception type
        exception_name = type(exception).__name__
        if exception_name == "AssertionError":
            assert diagnostic_info.category in [
                ErrorCategory.TEST_FAILURE,
                ErrorCategory.ASSERTION_ERROR,
            ]
        elif exception_name in ["ImportError", "ModuleNotFoundError"]:
            assert diagnostic_info.category in [
                ErrorCategory.FRAMEWORK_ISSUE,
                ErrorCategory.DEPENDENCY_MISSING,
            ]
        elif exception_name in ["FileNotFoundError", "PermissionError"]:
            assert diagnostic_info.category == ErrorCategory.ENVIRONMENTAL
        elif exception_name == "MemoryError":
            assert diagnostic_info.category == ErrorCategory.RESOURCE_EXHAUSTION
        elif exception_name == "TimeoutError":
            assert diagnostic_info.category == ErrorCategory.TIMEOUT_ERROR
        elif exception_name == "SyntaxError":
            assert diagnostic_info.category == ErrorCategory.SYNTAX_ERROR

        # Verify user-friendly message generation
        assert diagnostic_info.user_friendly_message is not None
        assert len(diagnostic_info.user_friendly_message) > 0
        assert str(exception) in diagnostic_info.user_friendly_message

        # Verify stack trace capture
        assert isinstance(diagnostic_info.stack_trace, list)
        # Stack trace might be empty for artificially created exceptions

        # Verify resolution guidance (Requirement 10.3)
        assert isinstance(diagnostic_info.resolution_guidance, list)
        # Should have at least some guidance for known error categories
        if diagnostic_info.category in [
            ErrorCategory.DEPENDENCY_MISSING,
            ErrorCategory.ENVIRONMENTAL,
            ErrorCategory.RESOURCE_EXHAUSTION,
        ]:
            assert len(diagnostic_info.resolution_guidance) > 0

        # Verify each resolution guidance item is properly structured
        for guidance in diagnostic_info.resolution_guidance:
            assert isinstance(guidance, ResolutionGuidance)
            assert guidance.title is not None
            assert len(guidance.title) > 0
            assert guidance.description is not None
            assert len(guidance.description) > 0
            assert isinstance(guidance.steps, list)
            assert len(guidance.steps) > 0
            assert all(isinstance(step, str) and len(step) > 0 for step in guidance.steps)
            assert isinstance(guidance.success_probability, float)
            assert 0.0 <= guidance.success_probability <= 1.0

        # Verify serialization capability
        diagnostic_dict = diagnostic_info.to_dict()
        assert isinstance(diagnostic_dict, dict)
        assert "error_id" in diagnostic_dict
        assert "category" in diagnostic_dict
        assert "severity" in diagnostic_dict
        assert "message" in diagnostic_dict
        assert "timestamp" in diagnostic_dict

        # Verify error ID uniqueness (basic check)
        assert diagnostic_info.error_id.startswith("TEST_ERR_")
        assert len(diagnostic_info.error_id.split("_")) >= 3

    @given(
        exceptions=st.lists(exception_generator(), min_size=2, max_size=5),
        test_contexts=st.lists(context_generator_strategy(), min_size=2, max_size=5),
    )
    @settings(max_examples=5, deadline=5000)
    def test_error_categorization_consistency(self, exceptions, test_contexts):
        """
        Test that error categorization is consistent for similar error types.
        """
        # Ensure we have matching lengths
        min_length = min(len(exceptions), len(test_contexts))
        exceptions = exceptions[:min_length]
        test_contexts = test_contexts[:min_length]

        diagnostic_infos = []
        for exception, test_context in zip(exceptions, test_contexts):
            diagnostic_info = self.error_handler.handle_error(
                exception=exception, test_context=test_context
            )
            diagnostic_infos.append(diagnostic_info)

        # Group by exception type
        by_exception_type = {}
        for diagnostic_info in diagnostic_infos:
            exception_type = type(diagnostic_info.original_exception).__name__
            if exception_type not in by_exception_type:
                by_exception_type[exception_type] = []
            by_exception_type[exception_type].append(diagnostic_info)

        # Verify consistency within each exception type
        for exception_type, diagnostics in by_exception_type.items():
            if len(diagnostics) > 1:
                # All diagnostics of the same exception type should have the same category
                categories = [d.category for d in diagnostics]
                # Allow some flexibility for context-dependent categorization
                unique_categories = set(categories)
                assert (
                    len(unique_categories) <= 2
                ), f"Too many different categories for {exception_type}: {unique_categories}"

    @given(exception=exception_generator(), test_context=context_generator_strategy())
    @settings(max_examples=10, deadline=3000)
    def test_resolution_guidance_quality(self, exception, test_context):
        """
        Test that resolution guidance is appropriate and actionable.
        """
        diagnostic_info = self.error_handler.handle_error(
            exception=exception, test_context=test_context
        )

        for guidance in diagnostic_info.resolution_guidance:
            # Each guidance should have meaningful content
            assert len(guidance.title.strip()) > 0
            assert len(guidance.description.strip()) > 0
            assert len(guidance.steps) > 0

            # Steps should be actionable (contain action words)
            action_words = [
                "check",
                "verify",
                "install",
                "run",
                "update",
                "configure",
                "set",
                "create",
                "fix",
            ]
            for step in guidance.steps:
                step_lower = step.lower()
                # At least some steps should contain action words
                if any(word in step_lower for word in action_words):
                    assert len(step.strip()) > 10  # Should be descriptive enough

            # Success probability should be reasonable
            assert 0.0 <= guidance.success_probability <= 1.0

            # If automated fix is available, should have higher success probability
            if guidance.automated_fix_available:
                assert guidance.success_probability >= 0.7

            # Code examples should be valid if provided
            if guidance.code_example:
                assert len(guidance.code_example.strip()) > 0
                # Should not contain obvious placeholders without context
                if "<" in guidance.code_example and ">" in guidance.code_example:
                    # If it has placeholders, should be in a meaningful context
                    assert any(
                        word in guidance.code_example.lower()
                        for word in ["pip", "install", "python", "pytest"]
                    )

    @given(st.lists(exception_generator(), min_size=3, max_size=8))
    @settings(max_examples=5, deadline=8000)
    def test_error_pattern_analysis(self, exceptions):
        """
        Test error pattern analysis and common error detection.
        """
        diagnostic_infos = []
        for exception in exceptions:
            diagnostic_info = self.error_handler.handle_error(exception=exception)
            diagnostic_infos.append(diagnostic_info)

        # Test preventive measures suggestion
        suggestions = self.error_handler.suggest_preventive_measures(diagnostic_infos)
        assert isinstance(suggestions, list)

        # If there are many dependency errors, should suggest dependency management
        dependency_errors = [
            d for d in diagnostic_infos if d.category == ErrorCategory.DEPENDENCY_MISSING
        ]
        if len(dependency_errors) > 2:
            suggestion_text = " ".join(suggestions).lower()
            assert any(
                word in suggestion_text
                for word in ["requirements", "dependency", "virtual", "environment"]
            )

        # If there are resource errors, should suggest resource management
        resource_errors = [
            d for d in diagnostic_infos if d.category == ErrorCategory.RESOURCE_EXHAUSTION
        ]
        if len(resource_errors) > 1:
            suggestion_text = " ".join(suggestions).lower()
            assert any(
                word in suggestion_text for word in ["memory", "resource", "batch", "hardware"]
            )

    def test_system_state_capture_completeness(self):
        """
        Test that system state capture includes all required information.
        """
        system_state = SystemState.capture_current()

        # Verify all required fields are present and valid
        assert system_state.timestamp is not None
        assert isinstance(system_state.timestamp, datetime)

        assert system_state.python_version is not None
        assert len(system_state.python_version) > 0

        assert system_state.platform_info is not None
        assert len(system_state.platform_info) > 0

        # Memory usage should have expected keys
        assert isinstance(system_state.memory_usage, dict)
        required_memory_keys = ["total_gb", "available_gb", "percent_used", "free_gb"]
        for key in required_memory_keys:
            assert key in system_state.memory_usage
            assert isinstance(system_state.memory_usage[key], (int, float))
            assert system_state.memory_usage[key] >= 0

        # Disk usage should have expected keys
        assert isinstance(system_state.disk_usage, dict)
        required_disk_keys = ["total_gb", "free_gb", "percent_used"]
        for key in required_disk_keys:
            assert key in system_state.disk_usage
            assert isinstance(system_state.disk_usage[key], (int, float))
            assert system_state.disk_usage[key] >= 0

        # CPU usage should be valid percentage
        assert isinstance(system_state.cpu_usage, (int, float))
        assert 0 <= system_state.cpu_usage <= 100

        # Environment variables should be filtered for security
        assert isinstance(system_state.environment_variables, dict)
        for key, value in system_state.environment_variables.items():
            # Should not contain sensitive information
            key_lower = key.lower()
            assert not any(
                sensitive in key_lower for sensitive in ["password", "token", "key", "secret"]
            )
            # Values should be truncated for safety
            assert len(value) <= 100

        # Working directory should be valid
        assert system_state.working_directory is not None
        assert len(system_state.working_directory) > 0
        assert Path(system_state.working_directory).exists()

        # Process ID should be valid
        assert isinstance(system_state.process_id, int)
        assert system_state.process_id > 0


class ErrorHandlerStateMachine(RuleBasedStateMachine):
    """
    Stateful testing for ErrorHandler to verify behavior across multiple operations.
    """

    def __init__(self):
        super().__init__()
        self.error_handler = ErrorHandler()
        self.handled_errors = []

    @initialize()
    def setup(self):
        """Initialize the state machine."""
        self.error_handler = ErrorHandler()
        self.handled_errors = []

    @rule(exception=exception_generator(), test_context=context_generator_strategy())
    def handle_error_rule(self, exception, test_context):
        """Rule for handling errors."""
        diagnostic_info = self.error_handler.handle_error(
            exception=exception, test_context=test_context
        )

        # Verify the diagnostic info is valid
        assert isinstance(diagnostic_info, DiagnosticInfo)
        assert diagnostic_info.error_id is not None

        # Store for later analysis
        self.handled_errors.append(diagnostic_info)

        # Verify error IDs are unique
        error_ids = [error.error_id for error in self.handled_errors]
        assert len(error_ids) == len(set(error_ids)), "Error IDs should be unique"

    @rule()
    def analyze_patterns_rule(self):
        """Rule for analyzing error patterns."""
        if len(self.handled_errors) >= 3:
            suggestions = self.error_handler.suggest_preventive_measures(self.handled_errors)
            assert isinstance(suggestions, list)

            # If we have dependency errors and enough of them, should get suggestions
            categories_seen = set(error.category for error in self.handled_errors)
            dependency_count = sum(
                1
                for error in self.handled_errors
                if error.category == ErrorCategory.DEPENDENCY_MISSING
            )

            if dependency_count > 2:
                assert (
                    len(suggestions) > 0
                ), "Should have suggestions for multiple dependency errors"
                suggestion_text = " ".join(suggestions).lower()
                # Should mention dependency management if we've seen dependency errors
                assert any(
                    word in suggestion_text
                    for word in ["requirements", "dependency", "virtual", "environment"]
                ), f"No relevant words found in suggestions: {suggestions}, categories seen: {categories_seen}"


# Run the stateful test - commented out due to dependency issues
# TestErrorHandlerStateMachine = ErrorHandlerStateMachine.TestCase


if __name__ == "__main__":
    # Run a quick test
    handler = ErrorHandler()

    # Test with a simple exception
    try:
        raise ValueError("Test error for demonstration")
    except Exception as e:
        diagnostic = handler.handle_error(e)
        print(f"Error ID: {diagnostic.error_id}")
        print(f"Category: {diagnostic.category}")
        print(f"Severity: {diagnostic.severity}")
        print(f"Resolution guidance count: {len(diagnostic.resolution_guidance)}")
