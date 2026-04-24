"""
Property-based tests for anti-pattern detection system.

Tests the accuracy and completeness of anti-pattern detection in test code,
including AST-based analysis and improvement suggestion generation.
"""

from hypothesis import given, settings
from hypothesis import strategies as st

from apgi_framework.testing.anti_pattern_detector import (
    AntiPattern,
    AntiPatternDetector,
    AntiPatternType,
    ImprovementSuggestion,
    Severity,
)


# Test code generators
@st.composite
def valid_python_identifier(draw):
    """Generate valid Python identifiers."""
    first_char = draw(st.sampled_from("abcdefghijklmnopqrstuvwxyz_"))
    rest_chars = draw(
        st.text(
            alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_",
            max_size=10,
        )
    )
    return first_char + rest_chars


@st.composite
def function_with_no_assertions_strategy(draw):
    """Generate test functions without assertions."""
    func_name = draw(valid_python_identifier())
    if not func_name.startswith("test_"):
        func_name = "test_" + func_name

    body_lines = draw(
        st.lists(
            st.sampled_from(["x = 1", "y = 2", "result = x + y", "print('debug')", "pass"]),
            min_size=1,
            max_size=3,
        )
    )

    body = "\n    ".join(body_lines)

    return f"""
def {func_name}():
    {body}
"""


@st.composite
def function_with_many_assertions_strategy(draw):
    """Generate test functions with too many assertions."""
    func_name = draw(valid_python_identifier())
    if not func_name.startswith("test_"):
        func_name = "test_" + func_name

    num_assertions = draw(st.integers(min_value=11, max_value=15))
    assertions = []
    for i in range(num_assertions):
        assertions.append(f"assert {i} == {i}")

    body = "\n    ".join(assertions)

    return f"""
def {func_name}():
    {body}
"""


@st.composite
def function_with_sleep_strategy(draw):
    """Generate test functions with sleep calls."""
    func_name = draw(valid_python_identifier())
    if not func_name.startswith("test_"):
        func_name = "test_" + func_name

    sleep_time = draw(st.floats(min_value=0.1, max_value=5.0))

    return f"""
import time

def {func_name}():
    time.sleep({sleep_time})
    assert True
"""


@st.composite
def function_with_print_debugging_strategy(draw):
    """Generate test functions with print statements."""
    func_name = draw(valid_python_identifier())
    if not func_name.startswith("test_"):
        func_name = "test_" + func_name

    debug_message = draw(
        st.text(
            min_size=1,
            max_size=20,
            alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd")),
        )
    )

    return f"""
def {func_name}():
    print("{debug_message}")
    assert True
"""


@st.composite
def function_with_magic_numbers_strategy(draw):
    """Generate test functions with magic numbers."""
    func_name = draw(valid_python_identifier())
    if not func_name.startswith("test_"):
        func_name = "test_" + func_name

    magic_number = draw(
        st.integers(min_value=3, max_value=999).filter(lambda x: x not in [10, 100])
    )

    return f"""
def {func_name}():
    result = calculate_something()
    assert result == {magic_number}

def calculate_something():
    return {magic_number}
"""


@st.composite
def class_with_shared_state_strategy(draw):
    """Generate test classes with shared state issues."""
    class_name = draw(valid_python_identifier())
    if not class_name.startswith("Test"):
        class_name = "Test" + class_name

    var_name = draw(valid_python_identifier())
    var_value = draw(st.integers(min_value=1, max_value=100))

    return f"""
class {class_name}:
    {var_name} = {var_value}
    
    def test_something(self):
        assert self.{var_name} == {var_value}
"""


@st.composite
def function_with_broad_exceptions_strategy(draw):
    """Generate test functions with broad exception handling."""
    func_name = draw(valid_python_identifier())
    if not func_name.startswith("test_"):
        func_name = "test_" + func_name

    return f"""
def {func_name}():
    try:
        risky_operation()
        assert True
    except Exception:
        pass

def risky_operation():
    raise ValueError("Something went wrong")
"""


class TestAntiPatternDetectionProperties:
    """Property-based tests for AntiPatternDetector."""

    def setup_method(self):
        """Setup for each test method."""
        self.detector = AntiPatternDetector()

    # Feature: comprehensive-test-enhancement, Property 25: Anti-pattern detection accuracy
    @given(test_code=function_with_no_assertions_strategy())
    @settings(max_examples=10, deadline=3000)
    def test_no_assertions_detection_property(self, test_code):
        """
        **Property 25a: No assertions anti-pattern detection**

        For any test function without assertions, the system should correctly
        identify it as the NO_ASSERTIONS anti-pattern.

        **Validates: Requirements 10.4**
        """
        anti_patterns = self.detector.analyze_code(test_code, "test_file.py")

        # Should detect NO_ASSERTIONS pattern
        no_assertion_patterns = [
            p for p in anti_patterns if p.pattern_type == AntiPatternType.NO_ASSERTIONS
        ]

        assert len(no_assertion_patterns) > 0, "Should detect functions without assertions"

        # Verify pattern details
        pattern = no_assertion_patterns[0]
        assert pattern.severity in [Severity.HIGH, Severity.CRITICAL]
        assert "assertion" in pattern.message.lower()
        assert len(pattern.suggestions) > 0

        # Verify suggestions are appropriate
        for suggestion in pattern.suggestions:
            assert isinstance(suggestion, ImprovementSuggestion)
            assert len(suggestion.title) > 0
            assert len(suggestion.description) > 0
            assert suggestion.effort_level in ["low", "medium", "high"]
            assert suggestion.impact in ["low", "medium", "high"]

    @given(test_code=function_with_many_assertions_strategy())
    @settings(max_examples=10, deadline=3000)
    def test_too_many_assertions_detection_property(self, test_code):
        """
        **Property 25b: Too many assertions anti-pattern detection**

        For any test function with excessive assertions, the system should
        correctly identify it as the TOO_MANY_ASSERTIONS anti-pattern.

        **Validates: Requirements 10.4**
        """
        anti_patterns = self.detector.analyze_code(test_code, "test_file.py")

        # Should detect TOO_MANY_ASSERTIONS pattern
        too_many_patterns = [
            p for p in anti_patterns if p.pattern_type == AntiPatternType.TOO_MANY_ASSERTIONS
        ]

        assert len(too_many_patterns) > 0, "Should detect functions with too many assertions"

        # Verify pattern details
        pattern = too_many_patterns[0]
        assert pattern.severity in [Severity.MEDIUM, Severity.HIGH]
        assert "assertion" in pattern.message.lower()
        assert len(pattern.suggestions) > 0

        # Should suggest splitting the test
        suggestion_texts = [s.description.lower() for s in pattern.suggestions]
        assert any("split" in text or "break" in text for text in suggestion_texts)

    @given(test_code=function_with_sleep_strategy())
    @settings(max_examples=10, deadline=3000)
    def test_sleep_in_tests_detection_property(self, test_code):
        """
        **Property 25c: Sleep in tests anti-pattern detection**

        For any test function containing sleep calls, the system should
        correctly identify it as the SLEEP_IN_TESTS anti-pattern.

        **Validates: Requirements 10.4**
        """
        anti_patterns = self.detector.analyze_code(test_code, "test_file.py")

        # Should detect SLEEP_IN_TESTS pattern
        sleep_patterns = [
            p for p in anti_patterns if p.pattern_type == AntiPatternType.SLEEP_IN_TESTS
        ]

        assert len(sleep_patterns) > 0, "Should detect sleep calls in tests"

        # Verify pattern details
        pattern = sleep_patterns[0]
        assert pattern.severity == Severity.HIGH
        assert "sleep" in pattern.message.lower()
        assert len(pattern.suggestions) > 0

        # Should suggest proper synchronization
        suggestion_texts = [s.description.lower() for s in pattern.suggestions]
        assert any("synchronization" in text or "wait" in text for text in suggestion_texts)

    @given(test_code=function_with_print_debugging_strategy())
    @settings(max_examples=10, deadline=3000)
    def test_print_debugging_detection_property(self, test_code):
        """
        **Property 25d: Print debugging anti-pattern detection**

        For any test function containing print statements, the system should
        correctly identify it as the PRINT_DEBUGGING anti-pattern.

        **Validates: Requirements 10.4**
        """
        anti_patterns = self.detector.analyze_code(test_code, "test_file.py")

        # Should detect PRINT_DEBUGGING pattern
        print_patterns = [
            p for p in anti_patterns if p.pattern_type == AntiPatternType.PRINT_DEBUGGING
        ]

        assert len(print_patterns) > 0, "Should detect print statements in tests"

        # Verify pattern details
        pattern = print_patterns[0]
        assert pattern.severity == Severity.MEDIUM
        assert "print" in pattern.message.lower()
        assert len(pattern.suggestions) > 0

        # Should suggest logging
        suggestion_texts = [s.description.lower() for s in pattern.suggestions]
        assert any("log" in text for text in suggestion_texts)

    @given(test_code=function_with_magic_numbers_strategy())
    @settings(max_examples=10, deadline=3000)
    def test_magic_numbers_detection_property(self, test_code):
        """
        **Property 25e: Magic numbers anti-pattern detection**

        For any test function containing magic numbers, the system should
        correctly identify it as the MAGIC_NUMBERS anti-pattern.

        **Validates: Requirements 10.4**
        """
        anti_patterns = self.detector.analyze_code(test_code, "test_file.py")

        # Should detect MAGIC_NUMBERS pattern
        magic_patterns = [
            p for p in anti_patterns if p.pattern_type == AntiPatternType.MAGIC_NUMBERS
        ]

        assert len(magic_patterns) > 0, "Should detect magic numbers in tests"

        # Verify pattern details
        pattern = magic_patterns[0]
        assert pattern.severity == Severity.LOW
        assert "magic" in pattern.message.lower() or "number" in pattern.message.lower()
        assert len(pattern.suggestions) > 0

        # Should suggest named constants
        suggestion_texts = [s.description.lower() for s in pattern.suggestions]
        assert any("constant" in text or "named" in text for text in suggestion_texts)

    @given(test_code=class_with_shared_state_strategy())
    @settings(max_examples=10, deadline=3000)
    def test_shared_state_detection_property(self, test_code):
        """
        **Property 25f: Shared state anti-pattern detection**

        For any test class with shared state variables, the system should
        correctly identify it as the SHARED_STATE anti-pattern.

        **Validates: Requirements 10.4**
        """
        anti_patterns = self.detector.analyze_code(test_code, "test_file.py")

        # Should detect SHARED_STATE pattern
        shared_state_patterns = [
            p for p in anti_patterns if p.pattern_type == AntiPatternType.SHARED_STATE
        ]

        assert len(shared_state_patterns) > 0, "Should detect shared state in test classes"

        # Verify pattern details
        pattern = shared_state_patterns[0]
        assert pattern.severity == Severity.HIGH
        assert "shared" in pattern.message.lower() or "state" in pattern.message.lower()
        assert len(pattern.suggestions) > 0

        # Should suggest fixtures
        suggestion_texts = [s.description.lower() for s in pattern.suggestions]
        assert any("fixture" in text for text in suggestion_texts)

    @given(test_code=function_with_broad_exceptions_strategy())
    @settings(max_examples=10, deadline=3000)
    def test_broad_exception_handling_detection_property(self, test_code):
        """
        **Property 25g: Broad exception handling anti-pattern detection**

        For any test function with broad exception handling, the system should
        correctly identify it as the BROAD_EXCEPTION_HANDLING anti-pattern.

        **Validates: Requirements 10.4**
        """
        anti_patterns = self.detector.analyze_code(test_code, "test_file.py")

        # Should detect BROAD_EXCEPTION_HANDLING pattern
        broad_exception_patterns = [
            p for p in anti_patterns if p.pattern_type == AntiPatternType.BROAD_EXCEPTION_HANDLING
        ]

        assert len(broad_exception_patterns) > 0, "Should detect broad exception handling"

        # Verify pattern details
        pattern = broad_exception_patterns[0]
        assert pattern.severity == Severity.MEDIUM
        assert "exception" in pattern.message.lower()
        assert len(pattern.suggestions) > 0

        # Should suggest specific exceptions
        suggestion_texts = [s.description.lower() for s in pattern.suggestions]
        assert any("specific" in text for text in suggestion_texts)

    @given(
        test_codes=st.lists(
            st.one_of(
                function_with_no_assertions_strategy(),
                function_with_print_debugging_strategy(),
                function_with_magic_numbers_strategy(),
            ),
            min_size=2,
            max_size=5,
        )
    )
    @settings(max_examples=5, deadline=5000)
    def test_comprehensive_analysis_property(self, test_codes):
        """
        **Property 25h: Comprehensive analysis accuracy**

        For any collection of test code with multiple anti-patterns, the system
        should detect all patterns accurately and provide appropriate suggestions.

        **Validates: Requirements 10.4**
        """
        # Combine all test codes
        combined_code = "\n\n".join(test_codes)

        anti_patterns = self.detector.analyze_code(combined_code, "test_file.py")

        # Should detect multiple patterns
        assert len(anti_patterns) > 0, "Should detect anti-patterns in combined code"

        # Verify each pattern has proper structure
        for pattern in anti_patterns:
            assert isinstance(pattern, AntiPattern)
            assert isinstance(pattern.pattern_type, AntiPatternType)
            assert isinstance(pattern.severity, Severity)
            assert len(pattern.message) > 0
            assert len(pattern.location) > 0
            assert len(pattern.code_snippet) > 0
            assert isinstance(pattern.suggestions, list)

            # Each pattern should have at least one suggestion
            assert len(pattern.suggestions) > 0

            # Verify suggestion quality
            for suggestion in pattern.suggestions:
                assert isinstance(suggestion, ImprovementSuggestion)
                assert len(suggestion.title) > 0
                assert len(suggestion.description) > 0
                assert suggestion.effort_level in ["low", "medium", "high"]
                assert suggestion.impact in ["low", "medium", "high"]

        # Generate report and verify structure
        report = self.detector.generate_report(anti_patterns)
        assert isinstance(report, dict)
        assert "total_issues" in report
        assert "by_severity" in report
        assert "by_type" in report
        assert "recommendations" in report
        assert report["total_issues"] == len(anti_patterns)

        # Verify report statistics
        assert isinstance(report["by_severity"], dict)
        assert isinstance(report["by_type"], dict)
        assert isinstance(report["recommendations"], list)

        # Total counts should match
        severity_total = sum(report["by_severity"].values())
        type_total = sum(report["by_type"].values())
        assert severity_total == len(anti_patterns)
        assert type_total == len(anti_patterns)

    def test_suggestion_quality_property(self):
        """
        Test that all generated suggestions meet quality standards.
        """
        # Test with a known problematic code
        test_code = """
def test_bad_example():
    print("debugging")
    time.sleep(1)
    x = 42  # magic number
    # No assertions
"""

        anti_patterns = self.detector.analyze_code(test_code, "test_file.py")

        # Should detect multiple issues
        assert len(anti_patterns) > 0

        # Verify all suggestions meet quality standards
        for pattern in anti_patterns:
            for suggestion in pattern.suggestions:
                # Title should be actionable
                assert len(suggestion.title) > 5
                assert not suggestion.title.endswith(".")  # Should be a phrase, not sentence

                # Description should be helpful
                assert len(suggestion.description) > 10

                # Effort and impact should be realistic
                assert suggestion.effort_level in ["low", "medium", "high"]
                assert suggestion.impact in ["low", "medium", "high"]

                # If code example provided, should be valid Python (basic check)
                if suggestion.code_example:
                    assert len(suggestion.code_example.strip()) > 0
                    # Should not contain obvious placeholders without context
                    if "<" in suggestion.code_example and ">" in suggestion.code_example:
                        # If placeholders exist, should have some context
                        assert any(
                            word in suggestion.code_example.lower()
                            for word in ["assert", "def", "class", "import"]
                        )

    def test_report_generation_consistency(self):
        """
        Test that report generation is consistent and accurate.
        """
        # Create test code with known patterns
        test_code = """
def test_no_assertions():
    x = 1
    y = 2

def test_with_print():
    print("debug")
    assert True

class TestSharedState:
    shared_var = 42
    
    def test_something(self):
        assert self.shared_var == 42
"""

        anti_patterns = self.detector.analyze_code(test_code, "test_file.py")
        report = self.detector.generate_report(anti_patterns)

        # Verify report structure
        assert isinstance(report["total_issues"], int)
        assert report["total_issues"] > 0
        assert report["total_issues"] == len(anti_patterns)

        # Verify counts are consistent
        severity_sum = sum(report["by_severity"].values())
        type_sum = sum(report["by_type"].values())
        assert severity_sum == report["total_issues"]
        assert type_sum == report["total_issues"]

        # Verify recommendations are relevant
        if report["recommendations"]:
            for rec in report["recommendations"]:
                assert isinstance(rec, str)
                assert len(rec) > 10  # Should be meaningful

        # Verify issues list matches anti_patterns
        if "issues" in report:
            assert len(report["issues"]) == len(anti_patterns)


if __name__ == "__main__":
    # Run a quick test
    detector = AntiPatternDetector()

    # Test with problematic code
    test_code = """
def test_bad():
    print("debug")
    time.sleep(1)
    assert 42 == 42  # magic number
"""

    patterns = detector.analyze_code(test_code)
    print(f"Detected {len(patterns)} anti-patterns:")
    for pattern in patterns:
        print(f"- {pattern.pattern_type.value}: {pattern.message}")
        print(f"  Suggestions: {len(pattern.suggestions)}")
