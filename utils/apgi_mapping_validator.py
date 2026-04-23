import re
from pathlib import Path
from typing import Dict, List


class APGIMappingValidator:
    """
    Validates the mapping between mathematical equations in APGI_Equations.py
    and their corresponding unit tests.
    """

    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)
        self.equations_file = self.root_dir / "APGI_Equations.py"
        self.tests_dir = self.root_dir / "tests" / "unit"
        self.equation_pattern = re.compile(r"From Section ([\d\.]+)")
        self.test_ref_pattern = re.compile(r"APGI Eq\. ([\d\.]+)")

    def extract_equations(self) -> Dict[str, str]:
        """Extracts documented equation sections from APGI_Equations.py."""
        equations: Dict[str, str] = {}
        if not self.equations_file.exists():
            return equations

        current_method = None
        with open(self.equations_file, "r") as f:
            for line in f:
                method_match = re.search(r"def ([\w_]+)\(", line)
                if method_match:
                    current_method = method_match.group(1)

                section_match = self.equation_pattern.search(line)
                if section_match and current_method:
                    section_id = section_match.group(1)
                    equations[section_id] = current_method

        return equations

    def scan_tests(self) -> Dict[str, List[str]]:
        """Scans unit tests for references to APGI equations."""
        test_mappings: Dict[str, List[str]] = {}
        for test_file in self.tests_dir.glob("test_*.py"):
            with open(test_file, "r") as f:
                content = f.read()
                matches = self.test_ref_pattern.findall(content)
                for match in matches:
                    if match not in test_mappings:
                        test_mappings[match] = []
                    test_mappings[match].append(test_file.name)

        return test_mappings

    def validate(self) -> bool:
        """Performs validation and prints a report."""
        equations = self.extract_equations()
        test_mappings = self.scan_tests()

        print("APGI Code-to-Math Mapping Report")
        print("===============================")
        print(f"Found {len(equations)} documented equation sections in APGI_Equations.py")
        print(f"Found {len(test_mappings)} equation references in unit tests\n")

        covered = []
        missing = []

        for section_id, method in sorted(equations.items()):
            if section_id in test_mappings:
                covered.append((section_id, method, test_mappings[section_id]))
            else:
                missing.append((section_id, method))

        print("Covered Equations:")
        for section_id, method, files in covered:
            print(f"  [✓] Section {section_id} ({method}) -> {', '.join(files)}")

        print("\nMissing Test Coverage:")
        for section_id, method in missing:
            print(f"  [ ] Section {section_id} ({method})")

        total = len(equations)
        if total > 0:
            coverage = (len(covered) / total) * 100
            print(f"\nTotal Equation Coverage: {coverage:.1f}%")

        return len(missing) == 0


if __name__ == "__main__":
    validator = APGIMappingValidator(".")
    validator.validate()
