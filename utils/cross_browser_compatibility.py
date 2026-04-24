#!/usr/bin/env python3
"""
Cross-browser compatibility testing framework for APGI Framework web interfaces.

Provides automated testing across different browsers and platforms to ensure
consistent GUI behavior and compatibility.
"""

import json
import platform
import time
from pathlib import Path
from typing import Dict, List, Optional, cast, Any

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options as ChromeOptions
    from selenium.webdriver.firefox.options import Options as FirefoxOptions
    from selenium.webdriver.safari.options import Options as SafariOptions
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import WebDriverException, TimeoutException

    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

try:
    from apgi_framework.logging.standardized_logging import get_logger

    logger = get_logger(__name__)
except ImportError:
    import logging

    logger = logging.getLogger(__name__)  # type: ignore


class BrowserTestResult:
    """Container for browser test results."""

    def __init__(self, browser_name: str, platform_info: str):
        self.browser_name = browser_name
        self.platform_info = platform_info
        self.start_time = time.time()
        self.end_time: Optional[float] = None
        self.success: bool = False
        self.error_message: Optional[str] = None
        self.test_steps: List[Dict[str, str]] = []
        self.screenshots: List[str] = []
        self.performance_metrics: Dict[str, float] = {}

    def add_step(self, step_name: str, status: str, details: str = ""):
        """Add a test step result."""
        self.test_steps.append(
            {
                "step": step_name,
                "status": status,
                "details": details,
                "timestamp": time.time(),  # type: ignore
            }
        )

    def finish(self, success: bool, error_message: Optional[str] = None):
        """Mark test as finished."""
        self.end_time = time.time()
        self.success = success
        self.error_message = error_message

    def get_duration(self) -> float:
        """Get test duration in seconds."""
        end = self.end_time or time.time()
        return end - self.start_time

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "browser": self.browser_name,
            "platform": self.platform_info,
            "success": self.success,
            "duration": self.get_duration(),
            "error": self.error_message,
            "test_steps": self.test_steps,
            "screenshots": self.screenshots,
            "performance_metrics": self.performance_metrics,
        }


class CrossBrowserTester:
    """
    Cross-browser compatibility testing framework.

    Tests web interfaces across different browsers and platforms.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        screenshot_dir: str = "./test_screenshots",
    ):
        """
        Initialize cross-browser tester.

        Args:
            base_url: Base URL for testing
            screenshot_dir: Directory for storing screenshots
        """
        self.base_url = base_url
        self.screenshot_dir = Path(screenshot_dir)
        self.screenshot_dir.mkdir(exist_ok=True)

        self.platform_info = self._get_platform_info()
        self.available_browsers = self._detect_available_browsers()

        logger.info(f"CrossBrowserTester initialized for {self.platform_info}")
        logger.info(f"Available browsers: {list(self.available_browsers.keys())}")

    def _get_platform_info(self) -> str:
        """Get platform information string."""
        system = platform.system()
        version = platform.version()
        machine = platform.machine()
        return f"{system} {version} ({machine})"

    def _detect_available_browsers(self) -> Dict[str, bool]:
        """Detect available browsers on the system."""
        browsers: Dict[str, bool] = {}

        if not SELENIUM_AVAILABLE:
            logger.warning("Selenium not available, browser detection limited")
            return browsers

        # Test Chrome/Chromium
        try:
            options = ChromeOptions()
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")

            driver = webdriver.Chrome(options=options)
            driver.quit()
            browsers["chrome"] = True
            logger.info("Chrome browser detected and working")
        except (WebDriverException, Exception) as e:
            browsers["chrome"] = False
            logger.debug(f"Chrome not available: {e}")

        # Test Firefox
        try:
            options = cast(Any, FirefoxOptions())  # Cast to avoid type conflicts
            options.add_argument("--headless")

            driver = cast(Any, webdriver.Firefox(options=options))  # Cast to avoid type conflicts
            driver.quit()
            browsers["firefox"] = True
            logger.info("Firefox browser detected and working")
        except (WebDriverException, Exception) as e:
            browsers["firefox"] = False
            logger.debug(f"Firefox not available: {e}")

        # Test Safari (macOS only)
        if platform.system() == "Darwin":
            try:
                options = cast(Any, SafariOptions())  # Cast to avoid type conflicts
                driver = cast(
                    Any, webdriver.Safari(options=options)
                )  # Cast to avoid type conflicts
                driver.quit()
                browsers["safari"] = True
                logger.info("Safari browser detected and working")
            except (WebDriverException, Exception) as e:
                browsers["safari"] = False
                logger.debug(f"Safari not available: {e}")

        return browsers

    def test_browser_compatibility(
        self, test_urls: Optional[List[str]] = None
    ) -> Dict[str, BrowserTestResult]:
        """
        Run compatibility tests across all available browsers.

        Args:
            test_urls: List of URLs to test (defaults to common APGI pages)

        Returns:
            Dictionary of browser test results
        """
        if not SELENIUM_AVAILABLE:
            logger.error("Selenium not available - cannot run browser tests")
            return {}

        if test_urls is None:
            test_urls = [
                f"{self.base_url}/",
                f"{self.base_url}/gui",
                f"{self.base_url}/dashboard",
                f"{self.base_url}/experiments",
            ]

        results = {}

        for browser_name, is_available in self.available_browsers.items():
            if not is_available:
                logger.info(f"Skipping {browser_name} - not available")
                continue

            logger.info(f"Testing {browser_name} compatibility...")
            result = self._test_single_browser(browser_name, test_urls)
            results[browser_name] = result

            # Brief pause between browsers
            time.sleep(2)

        return results

    def _test_single_browser(self, browser_name: str, test_urls: List[str]) -> BrowserTestResult:
        """Test a single browser with the given URLs."""
        result = BrowserTestResult(browser_name, self.platform_info)

        try:
            driver = self._create_driver(browser_name)
            if not driver:
                result.finish(False, f"Could not create {browser_name} driver")
                return result

            try:
                # Test each URL
                for url in test_urls:
                    self._test_url(driver, url, result)

                # Test responsive design
                self._test_responsive_design(driver, result)

                # Test basic interactions
                self._test_basic_interactions(driver, result)

                result.finish(True)
                logger.info(f"{browser_name} compatibility test passed")

            finally:
                if driver:
                    cast(Any, driver).quit()  # Cast to avoid type conflicts

        except Exception as e:
            result.finish(False, str(e))
            logger.error(f"{browser_name} compatibility test failed: {e}")

        return result

    def _create_driver(self, browser_name: str) -> Optional[object]:  # type: ignore
        """Create WebDriver instance for the specified browser."""
        try:
            if browser_name == "chrome":
                options = ChromeOptions()
                options.add_argument("--headless")
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-dev-shm-usage")
                options.add_argument("--window-size=1920,1080")
                return webdriver.Chrome(options=options)

            elif browser_name == "firefox":
                options = FirefoxOptions()  # type: ignore
                options.add_argument("--headless")
                options.add_argument("--width=1920")
                options.add_argument("--height=1080")
                return webdriver.Firefox(options=options)  # type: ignore

            elif browser_name == "safari":
                options = SafariOptions()  # type: ignore
                return webdriver.Safari(options=options)  # type: ignore

        except Exception as e:
            logger.error(f"Failed to create {browser_name} driver: {e}")
            return None

    def _test_url(self, driver, url: str, result: BrowserTestResult):
        """Test a single URL."""
        step_name = f"Load {url}"

        try:
            # Measure load time
            start_time = time.time()
            driver.get(url)

            # Wait for page to load
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

            load_time = time.time() - start_time
            result.performance_metrics[f"{url}_load_time"] = load_time

            # Check for errors
            if "error" in driver.title.lower() or "500" in driver.page_source:
                result.add_step(step_name, "FAILED", "Error page detected")
                self._take_screenshot(driver, f"{step_name}_error", result)
            else:
                result.add_step(step_name, "PASSED", f"Loaded in {load_time:.2f}s")
                self._take_screenshot(driver, step_name, result)

        except TimeoutException:
            result.add_step(step_name, "FAILED", "Page load timeout")
            self._take_screenshot(driver, f"{step_name}_timeout", result)

        except Exception as e:
            result.add_step(step_name, "FAILED", str(e))

    def _test_responsive_design(self, driver, result: BrowserTestResult):
        """Test responsive design at different screen sizes."""
        step_name = "Responsive Design"

        try:
            screen_sizes = [
                (1920, 1080, "Desktop"),
                (768, 1024, "Tablet"),
                (375, 667, "Mobile"),
            ]

            for width, height, label in screen_sizes:
                driver.set_window_size(width, height)
                time.sleep(1)  # Allow for resize

                # Check if page is still functional
                try:
                    body = driver.find_element(By.TAG_NAME, "body")
                    if body.is_displayed():
                        result.add_step(
                            f"{step_name} - {label}",
                            "PASSED",
                            f"Responsive at {width}x{height}",
                        )
                        self._take_screenshot(driver, f"{step_name}_{label}", result)
                    else:
                        result.add_step(
                            f"{step_name} - {label}",
                            "FAILED",
                            "Body not visible after resize",
                        )
                except Exception as e:
                    result.add_step(f"{step_name} - {label}", "FAILED", str(e))

        except Exception as e:
            result.add_step(step_name, "FAILED", str(e))

    def _test_basic_interactions(self, driver, result: BrowserTestResult):
        """Test basic GUI interactions."""
        step_name = "Basic Interactions"

        try:
            # Test clicking common elements
            selectors_to_test = [
                ("button", "Buttons"),
                ("input[type='text']", "Text inputs"),
                ("select", "Dropdowns"),
                (".nav-item", "Navigation items"),
                (".btn", "Bootstrap buttons"),
            ]

            for selector, description in selectors_to_test:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        # Test first element if found
                        element = elements[0]
                        if element.is_displayed() and element.is_enabled():
                            # Try to click (without causing navigation)
                            driver.execute_script("arguments[0].scrollIntoView();", element)
                            time.sleep(0.5)

                            result.add_step(
                                f"{step_name} - {description}",
                                "PASSED",
                                f"Found {len(elements)} elements",
                            )
                        else:
                            result.add_step(
                                f"{step_name} - {description}",
                                "SKIPPED",
                                "Elements not visible/enabled",
                            )
                    else:
                        result.add_step(
                            f"{step_name} - {description}",
                            "SKIPPED",
                            "No elements found",
                        )

                except Exception as e:
                    result.add_step(f"{step_name} - {description}", "FAILED", str(e))

        except Exception as e:
            result.add_step(step_name, "FAILED", str(e))

    def _take_screenshot(self, driver, name: str, result: BrowserTestResult):
        """Take a screenshot and save it."""
        try:
            timestamp = int(time.time())
            filename = f"{name}_{timestamp}.png"
            filepath = self.screenshot_dir / filename

            driver.save_screenshot(str(filepath))
            result.screenshots.append(filename)

        except Exception as e:
            logger.warning(f"Failed to take screenshot {name}: {e}")

    def generate_report(
        self,
        results: Dict[str, BrowserTestResult],
        output_file: str = "browser_compatibility_report.json",
    ) -> str:
        """
        Generate compatibility test report.

        Args:
            results: Test results from test_browser_compatibility
            output_file: Output file path

        Returns:
            Path to generated report file
        """
        report_data = {
            "test_summary": {
                "timestamp": time.time(),
                "platform": self.platform_info,
                "base_url": self.base_url,
                "total_browsers_tested": len(results),
                "passed_browsers": sum(1 for r in results.values() if r.success),
                "failed_browsers": sum(1 for r in results.values() if not r.success),
            },
            "browser_results": {name: result.to_dict() for name, result in results.items()},
            "recommendations": self._generate_recommendations(results),
        }

        report_path = Path(output_file)
        with open(report_path, "w") as f:
            json.dump(report_data, f, indent=2)

        logger.info(f"Browser compatibility report saved to {report_path}")
        return str(report_path)

    def _generate_recommendations(self, results: Dict[str, BrowserTestResult]) -> List[str]:
        """Generate recommendations based on test results."""
        recommendations = []

        failed_browsers = [name for name, result in results.items() if not result.success]

        if failed_browsers:
            recommendations.append(f"Fix compatibility issues with: {', '.join(failed_browsers)}")

        # Check for common issues
        slow_load_times = []
        for name, result in results.items():
            for metric, value in result.performance_metrics.items():
                if "load_time" in metric and value > 5.0:  # 5 seconds threshold
                    slow_load_times.append(f"{name}: {metric} ({value:.2f}s)")

        if slow_load_times:
            recommendations.append("Optimize page load times for: " + ", ".join(slow_load_times))

        # Platform-specific recommendations
        if (
            platform.system() == "Darwin"
            and not results.get("safari", BrowserTestResult("", "")).success
        ):
            recommendations.append("Consider Safari-specific optimizations for macOS users")

        if len(results) < 3:
            recommendations.append(
                "Expand browser testing to cover more browsers for better compatibility"
            )

        if not recommendations:
            recommendations.append("All tested browsers show good compatibility!")

        return recommendations


def run_compatibility_tests(base_url: str = "http://localhost:8000") -> str:
    """
    Run full compatibility test suite.

    Args:
        base_url: Base URL to test

    Returns:
        Path to generated report
    """
    if not SELENIUM_AVAILABLE:
        logger.error("Selenium not available. Install with: pip install selenium")
        return ""

    tester = CrossBrowserTester(base_url)
    results = tester.test_browser_compatibility()
    report_path = tester.generate_report(results)

    # Print summary
    passed = sum(1 for r in results.values() if r.success)
    total = len(results)
    print("\nBrowser Compatibility Test Results:")
    print(f"Passed: {passed}/{total} browsers")

    for name, result in results.items():
        status = "✓ PASS" if result.success else "✗ FAIL"
        duration = result.get_duration()
        print(f"  {name}: {status} ({duration:.1f}s)")

    return report_path


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run cross-browser compatibility tests")
    parser.add_argument("--url", default="http://localhost:8000", help="Base URL to test")
    parser.add_argument("--screenshots", default="./test_screenshots", help="Screenshot directory")

    args = parser.parse_args()

    report = run_compatibility_tests(args.url)
    if report:
        print(f"\nDetailed report saved to: {report}")
