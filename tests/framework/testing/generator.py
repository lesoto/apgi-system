"""
Comprehensive Test Suite Generator for APGI Framework

This module provides automated test suite generation capabilities including:
- Test discovery and categorization
- Coverage analysis and gap identification
- Automated test case generation
- Test quality assessment
- Regression test detection
"""

import ast
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from apgi_framework.config import ConfigManager
from apgi_framework.logging.standardized_logging import get_logger

logger = get_logger(__name__)


@dataclass
class CoverageGap:
    """Represents a gap in test coverage."""

    module_name: str
    function_name: str
    function_type: str  # 'function', 'method', 'class'
    complexity_score: int
    test_priority: str  # 'high', 'medium', 'low'
    suggested_test_cases: List[str]


@dataclass
class SuiteMetrics:
    """Metrics for test suite quality assessment."""

    total_modules: int
    tested_modules: int
    total_functions: int
    tested_functions: int
    coverage_percentage: float
    test_quality_score: float
    complexity_score: float
    maintenance_index: float


class SuiteGenerator:
    """Comprehensive test suite generator and analyzer."""

    def __init__(self, config_manager: Optional[ConfigManager] = None):
        """Initialize the test suite generator."""
        self.config_manager = config_manager or ConfigManager()
        self.logger = get_logger(f"{__name__}.TestSuiteGenerator")

        # Test generation templates
        self.function_test_template = '''
def test_{function_name}():
    """Test function {function_name}."""
    # Function signature: {signature}
    # Complexity: {complexity}
    
    # Arrange
    # Set up test data and dependencies based on function requirements
    test_data = self._get_test_data_for_function("{function_name}")
    
    # Act
    # Call the function under test with appropriate arguments
    result = {function_name}(test_data)
    
    # Assert
    # Verify expected behavior based on function specifications
    assert result is not None, "Function should return a valid result"
    assert isinstance(result, expected_type), "Result should be of expected type"
'''

        self.class_test_template = '''
class Test{class_name}:
    """Test class for {class_name}."""
    
    def setup_method(self):
        """Set up test environment."""
        # Initialize test fixtures and mock objects
        self.test_config = self._get_test_config()
        self.mock_dependencies = self._setup_mocks()
    
    def teardown_method(self):
        """Clean up after tests."""
        # Clean up test artifacts and reset mocks
        if hasattr(self, 'mock_dependencies'):
            self._cleanup_mocks(self.mock_dependencies)
    
    {test_methods}
'''

    def analyze_codebase(self, root_path: Optional[Path] = None) -> Dict[str, Any]:
        """Analyze the codebase for test coverage gaps."""
        if root_path is None:
            root_path = Path.cwd()

        self.root_path: Path = root_path or Path.cwd()
        self.codebase_analysis: Dict[str, Any] = {
            "modules": {},
            "coverage_gaps": [],
            "metrics": None,
            "analysis_timestamp": datetime.now().isoformat(),
        }

        # Discover Python modules
        modules = self._discover_python_modules(self.root_path)

        for module_path in modules:
            try:
                module_analysis = self._analyze_module(module_path)
                if not isinstance(self.codebase_analysis, dict):
                    self.codebase_analysis = {}  # type: ignore[unreachable]
                self.codebase_analysis.setdefault("modules", {})[str(module_path)] = module_analysis

                # Identify coverage gaps
                gaps = self._identify_coverage_gaps(module_analysis)
                self.codebase_analysis["coverage_gaps"].extend(gaps)

            except Exception as e:
                self.logger.warning(f"Failed to analyze module {module_path}: {e}")

        # Calculate overall metrics
        self.codebase_analysis["coverage_metrics"] = self._calculate_suite_metrics(
            self.codebase_analysis
        )

        return self.codebase_analysis
        # Unreachable code suppressed

    def _discover_python_modules(self, root_path: Path) -> List[Path]:
        """Discover all Python modules in the codebase."""
        modules = []

        # Skip test directories and common non-test directories
        skip_dirs = {
            "tests",
            "test",
            "__pycache__",
            ".git",
            ".pytest_cache",
            "venv",
            "env",
        }

        for py_file in root_path.rglob("*.py"):
            # Skip files in test directories or with test-related names
            if any(skip_dir in py_file.parts for skip_dir in skip_dirs):
                continue
            if py_file.name.startswith("test_") or py_file.name.endswith("_test.py"):
                continue

            modules.append(py_file)

        return modules

    def _analyze_module(self, module_path: Path) -> Dict[str, Any]:
        """Analyze a single Python module."""
        try:
            with open(module_path, "r", encoding="utf-8") as f:
                content = f.read()

            tree = ast.parse(content)

            analysis: Dict[str, Any] = {
                "path": str(module_path),
                "module_name": self._get_module_name(module_path),
                "functions": [],
                "classes": [],
                "imports": [],
                "complexity_score": 0,
                "has_tests": False,
            }

            # Analyze AST nodes
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_analysis = self._analyze_function(node)
                    analysis["functions"].append(func_analysis)
                    analysis["complexity_score"] += func_analysis["complexity"]

                elif isinstance(node, ast.ClassDef):
                    class_analysis = self._analyze_class(node)
                    analysis["classes"].append(class_analysis)
                    analysis["complexity_score"] += class_analysis["complexity"]

                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    analysis["imports"].append(self._analyze_import(node))

            # Check if module has corresponding test file
            test_file_path = self._find_test_file(module_path)
            analysis["has_tests"] = test_file_path is not None
            analysis["test_file_path"] = str(test_file_path) if test_file_path else None

            return analysis

        except Exception as e:
            self.logger.error(f"Failed to analyze module {module_path}: {e}")
            return {
                "path": str(module_path),
                "module_name": self._get_module_name(module_path),
                "error": str(e),
                "has_tests": False,
            }

    def _analyze_function(self, node: ast.FunctionDef) -> Dict[str, Any]:
        """Analyze a function definition."""
        complexity = self._calculate_complexity(node)

        return {
            "name": node.name,
            "type": "function",
            "line_number": node.lineno,
            "signature": self._get_function_signature(node),
            "docstring": ast.get_docstring(node) or "",
            "complexity": complexity,
            "args_count": len(node.args.args),
            "has_return": self._has_return_statement(node),
            "has_exceptions": self._has_exception_handling(node),
            "is_async": isinstance(node, ast.AsyncFunctionDef),
        }

    def _analyze_class(self, node: ast.ClassDef) -> Dict[str, Any]:
        """Analyze a class definition."""
        methods = []
        complexity = 1  # Base complexity for class

        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                method_analysis = self._analyze_function(item)
                method_analysis["type"] = "method"
                methods.append(method_analysis)
                complexity += method_analysis["complexity"]

        return {
            "name": node.name,
            "type": "class",
            "line_number": node.lineno,
            "docstring": ast.get_docstring(node) or "",
            "complexity": complexity,
            "method_count": len(methods),
            "methods": methods,
            "base_classes": [base.id for base in node.bases if isinstance(base, ast.Name)],
            "has_init": any(method["name"] == "__init__" for method in methods),
        }

    def _analyze_import(self, node) -> Dict[str, Any]:
        """Analyze an import statement."""
        if isinstance(node, ast.Import):
            return {
                "type": "import",
                "names": [alias.name for alias in node.names],
                "line_number": node.lineno,
            }
        elif isinstance(node, ast.ImportFrom):
            return {
                "type": "import_from",
                "module": node.module,
                "names": [alias.name for alias in node.names],
                "line_number": node.lineno,
            }

        # Default case for unsupported import types

        return {
            "type": "unknown_import",
            "line_number": getattr(node, "lineno", 0),
        }

    def _calculate_complexity(self, node) -> int:
        """Calculate cyclomatic complexity of a node."""
        complexity = 1  # Base complexity

        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.With)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
            elif isinstance(child, ast.ListComp):
                complexity += 1

        return complexity

    def _get_function_signature(self, node: ast.FunctionDef) -> str:
        """Get the signature of a function."""
        args = []

        # Regular arguments
        for arg in node.args.args:
            args.append(arg.arg)

        # Default arguments
        if node.args.defaults:
            args.extend([f"={i}" for i in range(len(node.args.defaults))])

        # *args
        if node.args.vararg:
            args.append(f"*{node.args.vararg.arg}")

        # **kwargs
        if node.args.kwarg:
            args.append(f"**{node.args.kwarg.arg}")

        return f"{node.name}({', '.join(args)})"

    def _has_return_statement(self, node: ast.FunctionDef) -> bool:
        """Check if function has return statements."""
        for child in ast.walk(node):
            if isinstance(child, ast.Return):
                return True
        return False

    def _has_exception_handling(self, node: ast.FunctionDef) -> bool:
        """Check if function has exception handling."""
        for child in ast.walk(node):
            if isinstance(child, (ast.Try, ast.ExceptHandler)):
                return True
        return False

    def _get_module_name(self, module_path: Path) -> str:
        """Get module name from file path."""
        try:
            relative_path = module_path.relative_to(Path.cwd())
        except ValueError:
            # If the path is not relative to cwd, use the full path
            relative_path = module_path

        parts = list(relative_path.parts)

        # Remove .py extension
        if parts[-1].endswith(".py"):
            parts[-1] = parts[-1][:-3]

        # Convert path to module notation
        if parts[-1] == "__init__":
            parts = parts[:-1]

        return ".".join(parts)

    def _find_test_file(self, module_path: Path) -> Optional[Path]:
        """Find corresponding test file for a module."""
        # Try different test file naming conventions
        test_names = [f"test_{module_path.stem}.py", f"{module_path.stem}_test.py"]

        # Look in test directories
        potential_test_dirs = [
            module_path.parent / "tests",
            Path.cwd() / "tests",
            module_path.parent,
        ]

        for test_dir in potential_test_dirs:
            if not test_dir.exists():
                continue

            for test_name in test_names:
                test_file = test_dir / test_name
                if test_file.exists():
                    return test_file

        return None

    def _identify_coverage_gaps(self, module_analysis: Dict[str, Any]) -> List[CoverageGap]:
        """Identify test coverage gaps in a module."""
        gaps: List[CoverageGap] = []

        # Skip modules that have errors
        if "error" in module_analysis:
            return gaps

        # Check functions
        for func in module_analysis.get("functions", []):
            if not self._is_function_tested(func, module_analysis):
                priority = self._calculate_test_priority(func)
                suggested_cases = self._suggest_test_cases(func)

                gap = CoverageGap(
                    module_name=module_analysis["module_name"],
                    function_name=func["name"],
                    function_type=func["type"],
                    complexity_score=func["complexity"],
                    test_priority=priority,
                    suggested_test_cases=suggested_cases,
                )
                gaps.append(gap)

        # Check classes and methods
        for cls in module_analysis.get("classes", []):
            if not self._is_class_tested(cls, module_analysis):
                # Add gap for the class itself
                priority = self._calculate_test_priority(cls)
                suggested_cases = self._suggest_class_test_cases(cls)

                gap = CoverageGap(
                    module_name=module_analysis["module_name"],
                    function_name=cls["name"],
                    function_type=cls["type"],
                    complexity_score=cls["complexity"],
                    test_priority=priority,
                    suggested_test_cases=suggested_cases,
                )
                gaps.append(gap)

                # Check individual methods
                for method in cls.get("methods", []):
                    if not self._is_method_tested(method, cls, module_analysis):
                        priority = self._calculate_test_priority(method)
                        suggested_cases = self._suggest_test_cases(method)

                        gap = CoverageGap(
                            module_name=module_analysis["module_name"],
                            function_name=f"{cls['name']}.{method['name']}",
                            function_type=method["type"],
                            complexity_score=method["complexity"],
                            test_priority=priority,
                            suggested_test_cases=suggested_cases,
                        )
                        gaps.append(gap)

        return gaps

    def _is_function_tested(self, func: Dict[str, Any], module_analysis: Dict[str, Any]) -> bool:
        """Check if a function is already tested."""
        if not module_analysis.get("has_tests"):
            return False

        test_file_path = module_analysis.get("test_file_path")
        if not test_file_path:
            return False

        try:
            with open(test_file_path, "r") as f:
                test_content = f.read()

            # Look for test function that references this function
            test_function_name = f"test_{func['name']}"
            return test_function_name in test_content or func["name"] in test_content

        except Exception:
            return False

    def _is_class_tested(self, cls: Dict[str, Any], module_analysis: Dict[str, Any]) -> bool:
        """Check if a class is already tested."""
        if not module_analysis.get("has_tests"):
            return False

        test_file_path = module_analysis.get("test_file_path")
        if not test_file_path:
            return False

        try:
            with open(test_file_path, "r") as f:
                test_content = f.read()

            # Look for test class
            test_class_name = f"Test{cls['name']}"
            return test_class_name in test_content or cls["name"] in test_content

        except Exception:
            return False

    def _is_method_tested(
        self,
        method: Dict[str, Any],
        cls: Dict[str, Any],
        module_analysis: Dict[str, Any],
    ) -> bool:
        """Check if a method is already tested."""
        if not module_analysis.get("has_tests"):
            return False

        test_file_path = module_analysis.get("test_file_path")
        if not test_file_path:
            return False

        try:
            with open(test_file_path, "r") as f:
                test_content = f.read()

            # Look for test method
            test_method_name = f"test_{method['name']}"
            return test_method_name in test_content or method["name"] in test_content

        except Exception:
            return False

    def _calculate_test_priority(self, item: Dict[str, Any]) -> str:
        """Calculate testing priority based on complexity and importance."""
        complexity = item.get("complexity", 1)

        # High priority for complex functions
        if complexity >= 10:
            return "high"
        # Medium priority for moderate complexity
        elif complexity >= 5:
            return "medium"
        # Low priority for simple functions
        else:
            return "low"

    def _suggest_test_cases(self, func: Dict[str, Any]) -> List[str]:
        """Suggest test cases for a function."""
        suggestions = []

        # Basic functionality test
        suggestions.append(f"Test basic functionality of {func['name']}")

        # Edge cases based on arguments
        if func["args_count"] > 0:
            suggestions.append("Test with valid arguments")
            suggestions.append("Test with invalid/None arguments")

        # Exception handling
        if func.get("has_exceptions"):
            suggestions.append("Test exception handling scenarios")

        # Return value testing
        if func.get("has_return"):
            suggestions.append("Test return value validation")

        # Async functions
        if func.get("is_async"):
            suggestions.append("Test async execution")

        return suggestions

    def _suggest_class_test_cases(self, cls: Dict[str, Any]) -> List[str]:
        """Suggest test cases for a class."""
        suggestions = []

        suggestions.append("Test class instantiation")
        suggestions.append("Test class initialization parameters")

        if cls.get("has_init"):
            suggestions.append("Test __init__ method with valid parameters")
            suggestions.append("Test __init__ method with invalid parameters")

        # Test key methods
        for method in cls.get("methods", []):
            if method["name"].startswith("__"):
                continue  # Skip dunder methods for basic suggestions
            suggestions.append(f"Test {method['name']} method")

        return suggestions

    def _calculate_suite_metrics(self, codebase_analysis: Dict[str, Any]) -> SuiteMetrics:
        """Calculate overall test suite metrics."""
        total_modules = len(codebase_analysis["modules"])
        tested_modules = sum(
            1 for mod in codebase_analysis["modules"].values() if mod.get("has_tests", False)
        )

        total_functions = 0
        tested_functions = 0
        total_complexity = 0

        for mod in codebase_analysis["modules"].values():
            if "error" in mod:
                continue

            # Count functions
            functions = mod.get("functions", [])
            total_functions += len(functions)

            # Count class methods
            for cls in mod.get("classes", []):
                total_functions += len(cls.get("methods", []))

            total_complexity += mod.get("complexity_score", 0)

        # Estimate tested functions based on coverage gaps
        all_items = []
        for mod in codebase_analysis["modules"].values():
            if "error" in mod:
                continue

            all_items.extend(mod.get("functions", []))
            for cls in mod.get("classes", []):
                all_items.append(cls)
                all_items.extend(cls.get("methods", []))

        # Count untested items
        untested_count = len(codebase_analysis["coverage_gaps"])
        tested_functions = max(0, len(all_items) - untested_count)

        # Calculate coverage percentage
        coverage_percentage = (
            (tested_functions / total_functions * 100) if total_functions > 0 else 0
        )

        # Calculate quality scores
        module_coverage_ratio = (tested_modules / total_modules) if total_modules > 0 else 0
        test_quality_score = min(100, coverage_percentage + (module_coverage_ratio * 20))
        complexity_score = total_complexity
        maintenance_index = max(0, 100 - (total_complexity / max(1, total_functions) * 10))

        return SuiteMetrics(
            total_modules=total_modules,
            tested_modules=tested_modules,
            total_functions=total_functions,
            tested_functions=tested_functions,
            coverage_percentage=coverage_percentage,
            test_quality_score=test_quality_score,
            complexity_score=complexity_score,
            maintenance_index=maintenance_index,
        )

    def generate_missing_tests(
        self, codebase_analysis: Dict[str, Any], output_dir: str = "generated_tests"
    ) -> Dict[str, str]:
        """Generate test files for missing test coverage."""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        generated_files = {}

        # Group gaps by module
        gaps_by_module: Dict[str, List[CoverageGap]] = {}
        for gap in codebase_analysis["coverage_gaps"]:
            module_name = gap.module_name
            if module_name not in gaps_by_module:
                gaps_by_module[module_name] = []
            gaps_by_module[module_name].append(gap)

        # Generate test files
        for module_name, gaps in gaps_by_module.items():
            test_file_content = self._generate_test_file(module_name, gaps)
            test_file_path = output_path / f"test_{module_name.replace('.', '_')}.py"

            with open(test_file_path, "w") as f:
                f.write(test_file_content)

            generated_files[module_name] = str(test_file_path)
            self.logger.info(f"Generated test file: {test_file_path}")

        return generated_files

    def _generate_test_file(self, module_name: str, gaps: List[CoverageGap]) -> str:
        """Generate a test file for a specific module."""
        content = f'''"""
Auto-generated tests for {module_name}

Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Total gaps: {len(gaps)}
"""

import pytest
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the module under test
try:
    import {module_name}
except ImportError as e:
    pytest.skip(f"Cannot import {module_name}: {{e}}", allow_module_level=True)

'''

        # Group gaps by type (functions vs classes)
        functions = [gap for gap in gaps if gap.function_type == "function"]
        classes = [gap for gap in gaps if gap.function_type == "class"]
        methods = [
            gap for gap in gaps if "." in gap.function_name and gap.function_type == "method"
        ]

        # Generate function tests
        for func_gap in functions:
            test_content = self._generate_function_test(func_gap)
            content += test_content + "\n\n"

        # Generate class tests
        for class_gap in classes:
            test_content = self._generate_class_test(class_gap)
            content += test_content + "\n\n"

        # Generate method tests
        for method_gap in methods:
            test_content = self._generate_method_test(method_gap)
            content += test_content + "\n\n"

        return content

    def _generate_function_test(self, gap: CoverageGap) -> str:
        """Generate test for a function."""
        return f'''def test_{gap.function_name}():
    """Test function {gap.function_name}.
    
    Priority: {gap.test_priority}
    Complexity: {gap.complexity_score}
    
    Suggested test cases:
    {chr(10).join(f"    - {case}" for case in gap.suggested_test_cases)}
    """
    # Auto-generated test implementation for {gap.function_name}
    
    # Arrange
    # Set up test data based on function requirements and suggested test cases
    test_args = self._prepare_test_arguments("{gap.function_name}")
    
    # Act
    # Call the function under test with prepared arguments
    result = {gap.function_name}(*test_args)
    
    # Assert
    # Verify expected behavior based on function specifications
    assert result is not None, f"Function {gap.function_name} should return a valid result"
    # Add specific assertions based on function behavior
    self._validate_function_result("{gap.function_name}", result)'''

    def _generate_class_test(self, gap: CoverageGap) -> str:
        """Generate test for a class."""
        return f'''class Test{gap.function_name}:
    """Test class for {gap.function_name}.
    
    Priority: {gap.test_priority}
    Complexity: {gap.complexity_score}
    """
    
    def setup_method(self):
        """Set up test environment."""
        # Initialize test fixtures and mock objects
        self.test_instance = None
        self.mock_dependencies = {{}}
    
    def teardown_method(self):
        """Clean up after tests."""
        # Clean up test artifacts and reset mocks
        if hasattr(self, 'test_instance') and self.test_instance:
            del self.test_instance
        if hasattr(self, 'mock_dependencies'):
            self.mock_dependencies.clear()
    
    def test_instantiation(self):
        """Test class instantiation."""
        # Test class initialization with default parameters
        try:
            self.test_instance = {gap.function_name}()
            assert self.test_instance is not None, "Class should instantiate successfully"
            assert isinstance(self.test_instance, {gap.function_name}), "Instance should be of correct type"
        except Exception as e:
            assert False, f"Class instantiation failed: {{e}}"
    
    def test_initialization_parameters(self):
        """Test initialization with various parameters."""
        # Test with valid and invalid parameters
        valid_params = self._get_valid_test_params({gap.function_name})
        invalid_params = self._get_invalid_test_params({gap.function_name})
        
        # Test valid parameters
        for params in valid_params:
            try:
                instance = {gap.function_name}(**params)
                assert instance is not None, f"Should instantiate with params: {{params}}"
            except Exception as e:
                assert False, f"Valid params failed: {{params}}, error: {{e}}"
        
        # Test invalid parameters
        for params in invalid_params:
            try:
                instance = {gap.function_name}(**params)
                assert False, f"Should raise exception with invalid params: {{params}}"
            except (ValueError, TypeError, AssertionError):
                pass  # Expected to fail'''

    def _generate_method_test(self, gap: CoverageGap) -> str:
        """Generate test for a method."""
        class_name, method_name = gap.function_name.split(".", 1)

        return f'''def test_{class_name}_{method_name}():
    """Test method {gap.function_name}.
    
    Priority: {gap.test_priority}
    Complexity: {gap.complexity_score}
    
    Suggested test cases:
    {chr(10).join(f"    - {case}" for case in gap.suggested_test_cases)}
    """
    # Auto-generated test implementation for {gap.function_name}
    
    # Arrange
    # Set up test instance and data based on method requirements
    instance = {class_name}()
    test_args = self._prepare_method_test_arguments("{gap.function_name}")
    
    # Act
    # Call the method under test with prepared arguments
    result = instance.{method_name}(*test_args)
    
    # Assert
    # Verify expected behavior based on method specifications
    assert result is not None, f"Method {gap.function_name} should return a valid result"
    # Add method-specific validations
    self._validate_method_result("{gap.function_name}", result)'''

    def generate_coverage_report(
        self, codebase_analysis: Dict[str, Any], output_file: str = "coverage_report.md"
    ) -> str:
        """Generate a comprehensive coverage report."""
        metrics = codebase_analysis["metrics"]
        gaps = codebase_analysis["coverage_gaps"]

        report = f"""# APGI Framework Test Coverage Report

Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Executive Summary

- **Total Modules**: {metrics.total_modules}
- **Tested Modules**: {metrics.tested_modules}
- **Total Functions/Methods**: {metrics.total_functions}
- **Tested Functions/Methods**: {metrics.tested_functions}
- **Coverage Percentage**: {metrics.coverage_percentage:.1f}%
- **Test Quality Score**: {metrics.test_quality_score:.1f}/100
- **Overall Complexity**: {metrics.complexity_score}
- **Maintenance Index**: {metrics.maintenance_index:.1f}/100

## Coverage Breakdown

### Module Coverage
{metrics.tested_modules}/{metrics.total_modules} modules ({(metrics.tested_modules / metrics.total_modules * 100):.1f}%) have test files

### Function/Method Coverage
{metrics.tested_functions}/{metrics.total_functions} functions and methods ({metrics.coverage_percentage:.1f}%) are tested

## Coverage Gaps by Priority

### High Priority Gaps (Complexity >= 10)
"""

        high_priority = [gap for gap in gaps if gap.test_priority == "high"]
        for gap in high_priority[:20]:  # Limit to top 20
            report += f"""
- **{gap.module_name}.{gap.function_name}** (Complexity: {gap.complexity_score})
  - Type: {gap.function_type}
  - Suggested tests: {len(gap.suggested_test_cases)}
"""

        report += """
### Medium Priority Gaps (Complexity 5-9)
"""

        medium_priority = [gap for gap in gaps if gap.test_priority == "medium"]
        for gap in medium_priority[:20]:  # Limit to top 20
            report += f"""
- **{gap.module_name}.{gap.function_name}** (Complexity: {gap.complexity_score})
  - Type: {gap.function_type}
  - Suggested tests: {len(gap.suggested_test_cases)}
"""

        report += """
### Low Priority Gaps (Complexity < 5)
"""

        low_priority = [gap for gap in gaps if gap.test_priority == "low"]
        for gap in low_priority[:20]:  # Limit to top 20
            report += f"""
- **{gap.module_name}.{gap.function_name}** (Complexity: {gap.complexity_score})
  - Type: {gap.function_type}
  - Suggested tests: {len(gap.suggested_test_cases)}
"""

        report += """
## Recommendations

1. **Immediate Actions** (High Priority):
   - Focus on high complexity functions that are currently untested
   - Implement tests for core functionality in critical modules
   - Add tests for error handling and edge cases

2. **Short-term Goals** (Medium Priority):
   - Improve coverage for utility functions
   - Add tests for class methods and properties
   - Implement integration tests for module interactions

3. **Long-term Improvements** (Low Priority):
   - Add tests for simple utility functions
   - Improve test documentation and examples
   - Implement performance and load testing

## Next Steps

To generate missing tests, run:
```bash
python -m apgi_framework.cli generate-tests --output-dir generated_tests
```

To run the generated tests:
```bash
python -m apgi_framework.cli batch-test --test-paths generated_tests/
```
"""

        # Save report
        with open(output_file, "w") as f:
            f.write(report)

        self.logger.info(f"Coverage report saved to {output_file}")
        return output_file


# Convenience functions
def analyze_test_coverage(root_path: Optional[Path] = None) -> Dict[str, Any]:
    """Analyze test coverage for the codebase."""
    generator = SuiteGenerator()
    return generator.analyze_codebase(root_path)


def generate_missing_tests(output_dir: str = "generated_tests") -> Dict[str, str]:
    """Generate tests for missing coverage."""
    generator = SuiteGenerator()
    analysis = generator.analyze_codebase()
    return generator.generate_missing_tests(analysis, output_dir)


def create_coverage_report(output_file: str = "coverage_report.md") -> str:
    """Create a comprehensive coverage report."""
    generator = SuiteGenerator()
    analysis = generator.analyze_codebase()
    return generator.generate_coverage_report(analysis, output_file)
