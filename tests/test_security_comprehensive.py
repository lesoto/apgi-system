"""
Comprehensive tests for security module.

Tests input validation, data structure validation, file path validation,
and security sanitization functions.
"""

import pytest
from pathlib import Path

from apgi_framework.security.security_validator import (
    SecurityValidator,
    SecurityError,
    validate_input,
    safe_eval_literal,
    validate_file_path,
    sanitize_for_logging,
)


class TestSecurityValidator:
    """Test suite for SecurityValidator."""

    def setup_method(self):
        """Set up test environment."""
        import tempfile

        self.temp_dir = Path(tempfile.mkdtemp())
        self.validator = SecurityValidator(strict_mode=True)

    def test_init_strict_mode(self):
        """Test validator initialization with strict mode."""
        validator = SecurityValidator(strict_mode=True)
        assert validator.strict_mode is True
        assert len(validator.validation_cache) == 0

    def test_init_non_strict_mode(self):
        """Test validator initialization with non-strict mode."""
        validator = SecurityValidator(strict_mode=False)
        assert validator.strict_mode is False
        assert len(validator.validation_cache) == 0

    def test_validate_string_input_safe(self):
        """Test validation of safe string input."""
        safe_strings = [
            "hello world",
            "user_123",
            "data.csv",
            "normal text content",
            "UPPERCASE text",
            "Mixed_Case_With_Underscores",
        ]

        for safe_string in safe_strings:
            assert self.validator.validate_string_input(safe_string, "test") is True

    def test_validate_string_input_dangerous_patterns(self):
        """Test validation of dangerous string patterns."""
        dangerous_patterns = [
            "__import__",
            "eval(",
            "exec(",
            "subprocess",
            "os.system",
            "open(",
            "file(",
            "input(",
            "raw_input(",
        ]

        for dangerous in dangerous_patterns:
            with pytest.raises(SecurityError, match=f"Dangerous pattern '{dangerous}' detected"):
                self.validator.validate_string_input(dangerous, "test")

    def test_validate_string_input_case_insensitive(self):
        """Test that string validation is case insensitive."""
        dangerous_variants = [
            "EXEC(",  # uppercase
            "Eval(",  # title case
            "IMPORT__",  # uppercase
            "__import__",  # lowercase
        ]

        for dangerous in dangerous_variants:
            with pytest.raises(SecurityError, match=f"Dangerous pattern '{dangerous}' detected"):
                self.validator.validate_string_input(dangerous, "test")

    def test_validate_string_input_non_string(self):
        """Test validation of non-string input."""
        non_string_inputs = [
            123,
            ["list", "of", "strings"],
            {"key": "value"},
            None,
            Path("/tmp/test"),
        ]

        for non_string in non_string_inputs:
            assert self.validator.validate_string_input(non_string, "test") is True

    def test_validate_data_structure_safe_types(self):
        """Test validation of safe data types."""
        safe_data = [
            "simple string",
            123,
            45.67,
            True,
            False,
            None,
            b"byte data",
            bytearray(b"byte array"),
            ["list", "of", "items"],
            ("tuple", "with", "items"),
            {"key": "value"},
            {"nested": {"data": "structure"}},
            set([1, 2, 3]),
            frozenset([1, 2, 3]),
        ]

        for data in safe_data:
            assert self.validator.validate_data_structure(data) is True

    def test_validate_data_structure_unsafe_strings(self):
        """Test validation of unsafe string data."""
        unsafe_strings = [
            "eval('dangerous')",
            "exec('malicious')",
            "__import__('os')",
            "subprocess.call('rm -rf /')",
            "open('/etc/passwd')",
        ]

        for unsafe in unsafe_strings:
            with pytest.raises(SecurityError, match=f"Dangerous pattern '{unsafe}' detected"):
                self.validator.validate_data_structure(unsafe)

    def test_validate_data_structure_nested_structures(self):
        """Test validation of nested data structures."""
        # Safe nested structure
        safe_nested = {
            "level1": {"level2": {"level3": "safe data"}, "list": ["item1", "item2"]},
            "top_list": [{"nested": {"data": "safe"}}, "simple_string"],
        }

        assert self.validator.validate_data_structure(safe_nested, max_depth=5) is True

        # Deep structure (exceeds max depth)
        deep_structure = {"level1": {"level2": {"level3": {"level4": {"level5": "too deep"}}}}}

        with pytest.raises(SecurityError, match="Data structure too deep"):
            self.validator.validate_data_structure(deep_structure, max_depth=3)

    def test_validate_file_path_safe_paths(self):
        """Test validation of safe file paths."""
        safe_paths = [
            "data.csv",
            "config.json",
            "output/results.txt",
            "subdir/file.txt",
            "./relative/path.txt",
            Path("relative/path.txt"),
            Path("/tmp/absolute/path.txt"),
        ]

        for path in safe_paths:
            assert self.validator.validate_file_path(path) is True

    def test_validate_file_path_traversal_attempts(self):
        """Test validation of path traversal attempts."""
        traversal_paths = [
            "../../../etc/passwd",
            "..\\..\\windows\\system32\\config\\sam",
            "/etc/shadow",
            "C:\\Windows\\System32\\drivers\\etc\\hosts",
            "data/../../../secret.txt",
            "folder/../../../../../etc/passwd",
        ]

        for traversal in traversal_paths:
            with pytest.raises(SecurityError, match="Directory traversal attempt detected"):
                self.validator.validate_file_path(traversal)

    def test_validate_file_path_system_paths(self):
        """Test validation of dangerous system paths."""
        system_paths = [
            "/etc/passwd",
            "/private/etc/ssh_host_keys",
            "/usr/bin/sudo",
            "/bin/bash",
            "/sbin/ifconfig",
            "/sys/kernel",
            "C:\\Windows\\System32",
            "C:\\Program Files",
            "C:\\System32\\drivers",
        ]

        for system_path in system_paths:
            with pytest.raises(SecurityError, match="Access to system path blocked"):
                self.validator.validate_file_path(system_path)

    def test_validate_file_path_allowed_directories(self):
        """Test validation with allowed base directories."""
        allowed_dirs = ["/tmp", "/home/user/data"]
        test_cases = [
            ("/tmp/safe.txt", True),  # Within allowed dir
            ("/home/user/data/file.txt", True),  # Within allowed dir
            ("/var/log/error.log", False),  # Outside allowed dirs
            ("/etc/passwd", False),  # System path
            ("../tmp/relative.txt", False),  # Traversal
        ]

        for path, expected in test_cases:
            result = self.validator.validate_file_path(path, allowed_base_dirs=allowed_dirs)
            assert result is expected

    def test_safe_literal_eval_safe_expressions(self):
        """Test safe literal evaluation."""
        safe_expressions = [
            "42",
            "['a', 'b', 'c']",
            "{'key': 'value'}",
            "{'nested': {'data': [1, 2, 3]}}",
            "{'list': ['item1', 'item2']}",
        ]

        for expr in safe_expressions:
            result = self.validator.safe_literal_eval(expr)
            assert result == eval(expr)  # Should match literal eval

    def test_safe_literal_eval_dangerous_expressions(self):
        """Test dangerous literal evaluation."""
        dangerous_expressions = [
            "__import__('os')",
            "eval('malicious code')",
            "exec('system command')",
            "__import__('subprocess').call('rm -rf /')",
        ]

        for dangerous in dangerous_expressions:
            with pytest.raises(SecurityError, match="Dangerous pattern '__import__' detected"):
                self.validator.safe_literal_eval(dangerous)

    def test_safe_literal_eval_invalid_syntax(self):
        """Test literal evaluation with invalid syntax."""
        invalid_expressions = [
            "invalid syntax [",
            "{'unclosed dict",
            "('unclosed tuple'",
            "function_call()",
        ]

        for invalid in invalid_expressions:
            with pytest.raises(SecurityError, match="Invalid literal expression"):
                self.validator.safe_literal_eval(invalid)

    def test_sanitize_for_logging_safe_data(self):
        """Test sanitization of safe data for logging."""
        safe_data = [
            "user logged in",
            "processing complete",
            "data value: 123",
            "normal message text",
        ]

        for data in safe_data:
            sanitized = self.validator.sanitize_for_logging(data)
            assert data in sanitized  # Should preserve safe data
            assert "REDACTED" not in sanitized

    def test_sanitize_for_logging_sensitive_patterns(self):
        """Test sanitization of sensitive data patterns."""
        sensitive_cases = [
            ("password=secret123", "password=[REDACTED]"),
            ("api_key=abc123", "api_key=[REDACTED]"),
            ("token=bearer_token", "token=[REDACTED]"),
            ("db_password=mypass", "db_password=[REDACTED]"),
            ("AWS_SECRET=secret", "aws_secret=[REDACTED]"),
            ("authorization=bearer xyz", "authorization=[REDACTED]"),
            ("session=abc123", "session=[REDACTED]"),
            ("mysql_password=pass", "mysql_password=[REDACTED]"),
            ("stripe_secret=sk_test", "stripe_secret=[REDACTED]"),
            ("private_key=-----BEGIN", "private_key=[REDACTED]"),
            ("access_token=token", "access_token=[REDACTED]"),
            ("gcp_key=secret", "gcp_key=[REDACTED]"),
            ("twilio_token=auth", "twilio_token=[REDACTED]"),
            ("sendgrid_key=api", "sendgrid_key=[REDACTED]"),
            ("credential=user:pass", "credential=[REDACTED]"),
            ("credentials=file", "credentials=[REDACTED]"),
            ("database_password=secret", "database_password=[REDACTED]"),
            ("sqlite_password=pass", "sqlite_password=[REDACTED]"),
            ("postgres_password=pass", "postgres_password=[REDACTED]"),
            ("azure_secret=value", "azure_secret=[REDACTED]"),
            ("auth_token=secret", "auth_token=[REDACTED]"),
            ("key=secret", "key=[REDACTED]"),
            ("secret_key=private", "secret_key=[REDACTED]"),
            ("secret=value", "secret=[REDACTED]"),
            ("bearer=token", "bearer=[REDACTED]"),
            ("auth=session", "auth=[REDACTED]"),
            ("session_data=abc", "session=[REDACTED]"),
        ]

        for input_data, expected in sensitive_cases:
            sanitized = self.validator.sanitize_for_logging(input_data)
            assert sanitized == expected

    def test_sanitize_for_logging_truncation(self):
        """Test data truncation in sanitization."""
        long_string = "x" * 2000  # Very long string
        sanitized = self.validator.sanitize_for_logging(long_string, max_length=100)

        assert len(sanitized) <= 103  # 100 + "..."
        assert sanitized.endswith("... [truncated]")
        assert sanitized[:97] == "x" * 97  # First 97 characters preserved

    def test_sanitize_for_logging_error_handling(self):
        """Test sanitization error handling."""
        error_cases = [None, 123, {"key": "value"}, Path("/tmp/test")]

        for error_input in error_cases:
            result = self.validator.sanitize_for_logging(error_input)
            assert result == "[SANITIZATION_ERROR]"

    def test_convenience_functions(self):
        """Test global convenience functions."""
        # Test validate_input
        assert validate_input("safe_string") is True
        with pytest.raises(SecurityError):
            validate_input("eval('dangerous')")

        # Test safe_eval_literal
        result = safe_eval_literal("{'key': 'value'}")
        assert result == {"key": "value"}

        # Test validate_file_path
        assert validate_file_path("safe/path.txt") is True
        with pytest.raises(SecurityError):
            validate_file_path("../../../etc/passwd")

        # Test sanitize_for_logging
        sanitized = sanitize_for_logging("password=secret")
        assert "password=[REDACTED]" in sanitized

    def test_validation_caching(self):
        """Test that validation results are cached."""
        validator = SecurityValidator(strict_mode=True)

        # First validation should cache result
        result1 = validator.validate_string_input("safe_string", "test")
        assert len(validator.validation_cache) == 1

        # Second validation of same input should use cache
        result2 = validator.validate_string_input("safe_string", "test")
        assert len(validator.validation_cache) == 1  # Same cache size
        assert result1 is result2  # Should be same object (cached)

    def test_non_strict_mode_warnings(self):
        """Test non-strict mode logs warnings instead of raising errors."""
        validator = SecurityValidator(strict_mode=False)

        # Should return False and log warning for dangerous input
        result = validator.validate_string_input("eval('dangerous')", "test")
        assert result is False

        # Should return False and log warning for dangerous path
        result = validator.validate_file_path("../../../etc/passwd")
        assert result is False
