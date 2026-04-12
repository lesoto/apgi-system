#!/usr/bin/env python3
"""
Detailed coverage gap analysis script.

This script analyzes coverage.json to provide detailed information about
uncovered code, categorized by module and gap type.
"""

import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict


class GapAnalyzer:
    """Analyze coverage gaps and classify them."""

    def __init__(self, coverage_file: str = "coverage.json"):
        """
        Initialize gap analyzer.

        Parameters
        ----------
        coverage_file : str
            Path to coverage.json file.
        """
        self.coverage_file = Path(coverage_file)
        self.gaps_by_module: dict[str, list[dict[str, Any]]] = defaultdict(list)
        self.gaps_by_type: dict[str, list[dict[str, Any]]] = defaultdict(list)

    def load_coverage_data(self) -> Dict[str, Any]:
        """
        Load coverage data from JSON file.

        Returns
        -------
        dict
            Coverage data dictionary.
        """
        if not self.coverage_file.exists():
            raise FileNotFoundError(f"Coverage file not found: {self.coverage_file}")

        with open(self.coverage_file, "r") as f:
            content = f.read().strip()
            if not content:
                raise ValueError(f"Coverage file is empty: {self.coverage_file}")
            return json.loads(content)

    def classify_gap(self, filename: str, line_num: int) -> str:
        """
        Classify a coverage gap by analyzing the code.

        Parameters
        ----------
        filename : str
            Path to source file.
        line_num : int
            Line number of gap.

        Returns
        -------
        str
            Gap type: 'error_path', 'edge_case', 'untested_logic', or 'unknown'.
        """
        try:
            with open(filename, "r") as f:
                lines = f.readlines()

            if line_num > len(lines):
                return "unknown"

            line = lines[line_num - 1].strip()

            # Classify based on code patterns
            if "raise" in line or "except" in line:
                return "error_path"
            elif "if" in line and any(kw in line for kw in ["None", "[]", "0", "empty"]):
                return "edge_case"
            elif any(kw in line for kw in ["def", "class", "return", "="]):
                return "untested_logic"
            else:
                return "unknown"

        except Exception:
            return "unknown"

    def analyze(self) -> Dict[str, Any]:
        """
        Perform comprehensive gap analysis.

        Returns
        -------
        dict
            Analysis results with gaps categorized by module and type.
        """
        data = self.load_coverage_data()

        for filename, file_data in data["files"].items():
            # Skip test files and GUI files
            if "test_" in filename or "_GUI" in filename or "apgi_gui" in filename:
                continue

            summary = file_data["summary"]
            if summary["percent_covered"] < 100:
                missing_lines = file_data.get("missing_lines", [])

                # Determine module category
                if "apgi_system/core" in filename:
                    module = "core"
                elif "apgi_system/experiments" in filename:
                    module = "experiments"
                elif "apgi_system/neural" in filename:
                    module = "neural"
                elif "apgi_system/ignition" in filename:
                    module = "ignition"
                elif "apgi_system/interoception" in filename:
                    module = "interoception"
                elif "apgi_system/self_model" in filename:
                    module = "self_model"
                elif "apgi_system/visualization" in filename:
                    module = "visualization"
                elif "api/routes" in filename:
                    module = "api_routes"
                elif "api/services" in filename:
                    module = "api_services"
                elif "api/middleware" in filename:
                    module = "api_middleware"
                elif "api/database" in filename:
                    module = "api_database"
                else:
                    module = "system"

                gap_info = {
                    "file": filename,
                    "coverage": summary["percent_covered"],
                    "missing_lines": missing_lines,
                    "num_missing": len(missing_lines),
                }

                self.gaps_by_module[module].append(gap_info)

                # Classify each gap
                for line_num in missing_lines:
                    gap_type = self.classify_gap(filename, line_num)
                    self.gaps_by_type[gap_type].append(
                        {
                            "file": filename,
                            "line": line_num,
                            "module": module,
                        }
                    )

        return {
            "by_module": dict(self.gaps_by_module),
            "by_type": dict(self.gaps_by_type),
            "total_files_with_gaps": sum(len(gaps) for gaps in self.gaps_by_module.values()),
            "total_missing_lines": sum(
                sum(gap["num_missing"] for gap in gaps) for gaps in self.gaps_by_module.values()
            ),
        }

    def print_report(self, analysis: Dict[str, Any]) -> None:
        """
        Print formatted analysis report.

        Parameters
        ----------
        analysis : dict
            Analysis results from analyze().
        """
        print("\n" + "=" * 80)
        print("DETAILED COVERAGE GAP ANALYSIS")
        print("=" * 80)

        print(f"\nTotal files with gaps: {analysis['total_files_with_gaps']}")
        print(f"Total missing lines: {analysis['total_missing_lines']}\n")

        # Report by module
        print("=" * 80)
        print("GAPS BY MODULE")
        print("=" * 80)

        for module, gaps in sorted(analysis["by_module"].items()):
            total_missing = sum(gap["num_missing"] for gap in gaps)
            print(f"\n{module.upper()}: {len(gaps)} files, {total_missing} missing lines")

            for gap in sorted(gaps, key=lambda x: x["num_missing"], reverse=True)[:5]:
                print(
                    f"  • {Path(gap['file']).name}: {gap['num_missing']} lines "
                    f"({gap['coverage']:.1f}% coverage)"
                )

            if len(gaps) > 5:
                print(f"  ... and {len(gaps) - 5} more files")

        # Report by gap type
        print("\n" + "=" * 80)
        print("GAPS BY TYPE")
        print("=" * 80)

        for gap_type, gaps in sorted(
            analysis["by_type"].items(), key=lambda x: len(x[1]), reverse=True
        ):
            print(f"\n{gap_type.upper()}: {len(gaps)} lines")

            # Group by module
            by_module: defaultdict[str, int] = defaultdict(int)
            for gap in gaps:
                by_module[gap["module"]] += 1

            for module, count in sorted(by_module.items(), key=lambda x: x[1], reverse=True):
                print(f"  • {module}: {count} lines")

        print("\n" + "=" * 80)


def main() -> int:
    """Main entry point."""
    try:
        analyzer = GapAnalyzer()
        analysis = analyzer.analyze()
        analyzer.print_report(analysis)

        # Save detailed report
        output_file = Path("coverage_gap_analysis.json")
        with open(output_file, "w") as f:
            json.dump(analysis, f, indent=2)

        print(f"\nDetailed analysis saved to: {output_file}")
        print("=" * 80 + "\n")

    except FileNotFoundError as e:
        print(f"\nError: {e}")
        print("Please run tests with coverage first: make test-coverage or pytest --cov\n")
        return 1

    except ValueError as e:
        print(f"\nError: {e}")
        print("Please run tests with coverage first: make test-coverage or pytest --cov\n")
        return 1

    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
