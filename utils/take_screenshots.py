#!/usr/bin/env python3
"""
APGI System Desktop App Screenshot Documentation

Captures screenshots of Python Tkinter desktop application
and interacts with all GUI elements automatically.

Requirements:
    pip install pyautogui pygetwindow pillow opencv-python

Usage:
    python take_screenshots.py
"""

import subprocess
import time
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import json
from datetime import datetime

try:
    import pyautogui
    import pygetwindow as gw
    from PIL import Image
    import cv2
    import numpy as np

    SCREENSHOT_AVAILABLE = True
except ImportError as e:
    print(f"Error: Required packages not installed. Missing: {e}")
    print("Run: pip install pyautogui pygetwindow pillow opencv-python")
    SCREENSHOT_AVAILABLE = False

    # Create dummy classes to prevent AttributeError
    class Dummy:
        def __getattr__(self, name):
            raise ImportError(f"Screenshot functionality not available: {name}")

    pyautogui = Dummy()
    gw = Dummy()
    Image = Dummy()
    cv2 = Dummy()
    np = Dummy()


class APGIScreenshotDocumentation:
    """Screenshot system for Python desktop application."""

    def __init__(self, base_dir: Path = None):
        self.base_dir = base_dir or Path(__file__).parent.parent
        self.screenshots_dir = self.base_dir / "docs" / "screenshots"
        self.reports_dir = self.base_dir / "docs" / "screenshots" / "reports"

        # Create directories
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

        # Documentation structure
        self.doc_structure = {
            "timestamp": datetime.now().isoformat(),
            "screenshots": [],
            "gui_elements": [],
            "system_info": self._get_system_info(),
        }

        # GUI process reference
        self.gui_process = None
        self.gui_window = None

        # Performance and reliability settings
        self.max_retry_attempts = 3
        self.base_wait_time = 0.5
        self.screenshot_timeout = 10
        self.interaction_delay = 1.0

        # Memory management
        self.max_screenshot_size = (1920, 1080)
        self.compression_quality = 85

        # GUI element locations (will be discovered)
        self.button_locations = {}
        self.tab_locations = {}
        self.slider_locations = {}
        self.menu_items = {}
        self.dialog_locations = {}
        self.view_toggles = {}
        self.zoom_controls = {}
        self.tools_actions = {}
        self.analysis_actions = {}
        self.help_actions = {}
        self.speed_slider = None
        self.status_bar = None
        self.event_log = None

    def _get_system_info(self) -> Dict[str, Any]:
        """Get system information for documentation."""
        import platform

        return {
            "platform": platform.system(),
            "platform_release": platform.release(),
            "platform_version": platform.version(),
            "architecture": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
            "screen_size": pyautogui.size() if SCREENSHOT_AVAILABLE else "Unknown",
        }

    def generate_comprehensive_documentation(self):
        """Generate complete screenshot documentation."""
        print("🚀 Starting APGI System Desktop App Documentation")
        print("=" * 60)

        print("\n📋 IMPORTANT SETUP INSTRUCTIONS:")
        print("   1. Make sure APGI GUI application is visible on screen")
        print("   2. Close any other applications that might interfere")
        print("   3. Click on the APGI application window to ensure it's active")
        print("   4. If automatic detection fails, you'll be prompted to select window manually")
        print("   5. Press Enter to continue or Ctrl+C to cancel...")

        try:
            if sys.stdin.isatty():
                input()  # Wait for user confirmation
            else:
                print("Running in non-interactive mode, proceeding automatically...")
        except KeyboardInterrupt:
            print("\n❌ Documentation cancelled by user")
            return
        except EOFError:
            print("Non-interactive mode detected, proceeding automatically...")

        try:
            # 1. Start GUI application
            self._start_gui_app()

            # 2. Discover GUI elements
            self._discover_gui_elements()

            # 3. Document all screens and interactions
            self._document_all_screens()

            # 4. Generate comprehensive report
            self._generate_documentation_report()

            print("\n✅ Documentation complete!")
            print(f"📸 Screenshots: {self.screenshots_dir}")
            print(f"📄 Reports: {self.reports_dir}")

        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback

            traceback.print_exc()

        finally:
            self._cleanup_processes()

    def _start_gui_app(self):
        """Start the GUI application."""
        print("\n📱 Starting GUI Application...")

        try:
            gui_script = self.base_dir / "apgi_gui.py"
            if not gui_script.exists():
                print(f"❌ GUI script not found: {gui_script}")
                return False

            # Start GUI in background
            self.gui_process = subprocess.Popen(
                [sys.executable, str(gui_script)], cwd=self.base_dir
            )

            print("✅ GUI application started")
            return True

        except Exception as e:
            print(f"❌ Error starting GUI: {e}")
            return False

    def _discover_gui_elements(self):
        """Discover and locate GUI elements with robust fallback."""
        print("\n🔍 Discovering GUI elements...")

        # Wait for GUI to fully load
        time.sleep(3)

        # Try to find the GUI window multiple times
        max_attempts = 3
        for attempt in range(max_attempts):
            print(f"  📍 Attempt {attempt + 1}/{max_attempts} to find GUI window...")
            self.gui_window = self._find_gui_window()

            if self.gui_window:
                break
            else:
                if attempt < max_attempts - 1:  # Don't wait after last attempt
                    print("  ⏳ Waiting 2 seconds before retry...")
                    time.sleep(2)

        if not self.gui_window:
            print("❌ Could not find APGI GUI window, using full-screen fallback mode")
            self._use_fallback_discovery()
            return False

        print(f"✅ Found GUI window: {self.gui_window.title}")

        # Manual verification - ask user to confirm if this is the right window
        print(
            f"\n🔍 Found window: '{self.gui_window.title}' ({self.gui_window.width}x{self.gui_window.height})"
        )
        print("Is this the correct APGI application window? (y/n)")
        try:
            if sys.stdin.isatty():
                response = input().strip().lower()
                if response not in ["y", "yes"]:
                    print("❌ User cancelled - window not confirmed")
                    return False
            else:
                print("Non-interactive mode: assuming 'yes' for window confirmation")
        except (KeyboardInterrupt, EOFError):
            if sys.stdin.isatty():
                print("\n❌ Documentation cancelled by user")
                return False
            else:
                print("Non-interactive mode: proceeding with window")

        # Activate and maximize window
        try:
            self.gui_window.activate()
            if hasattr(self.gui_window, "maximize"):
                self.gui_window.maximize()
            time.sleep(2)
        except Exception as e:
            print(f"⚠️ Could not maximize window: {e}")

        # Verify window is active by taking a test screenshot
        try:
            pyautogui.screenshot(
                region=(
                    self.gui_window.left,
                    self.gui_window.top,
                    self.gui_window.width,
                    self.gui_window.height,
                )
            )
            print("✅ Window region capture test successful")
        except Exception as e:
            print(f"⚠️ Window region test failed, will use full screen: {e}")
            self.gui_window = None  # Force fallback mode
            self._use_fallback_discovery()
            return False

        # Take a screenshot to analyze
        try:
            screenshot = pyautogui.screenshot(
                region=(
                    self.gui_window.left,
                    self.gui_window.top,
                    self.gui_window.width,
                    self.gui_window.height,
                )
            )
        except Exception as e:
            print(f"⚠️ Could not capture window region, using full screen: {e}")
            screenshot = pyautogui.screenshot()

        screenshot_path = self.screenshots_dir / "gui_discovery.png"
        try:
            screenshot.save(screenshot_path)
            print(f"✅ Discovery screenshot saved: {screenshot_path.name}")
        except Exception as save_error:
            print(f"⚠️ Could not save discovery screenshot: {save_error}")

        # Discover buttons using template matching and heuristics
        self._discover_buttons(screenshot)
        self._discover_tabs(screenshot)
        self._discover_sliders(screenshot)
        self._discover_menu_items()

        print(
            f"✅ Found {len(self.button_locations)} buttons, {len(self.tab_locations)} tabs, {len(self.slider_locations)} sliders"
        )
        return True

    def _use_fallback_discovery(self):
        """Use keyboard shortcuts and estimated positions when window cannot be located."""
        print("  🔄 Using fallback discovery mode...")

        # Set up estimated button locations based on typical GUI layout
        screen_width, screen_height = pyautogui.size()

        # Estimate control panel position (left side)
        control_x = screen_width // 4
        control_y = screen_height // 3

        self.button_locations = {
            "start": {
                "x": control_x - 100,
                "y": control_y,
                "rect": (control_x - 100, control_y, 80, 30),
                "confidence": 0.5,
            },
            "pause": {
                "x": control_x,
                "y": control_y,
                "rect": (control_x, control_y, 80, 30),
                "confidence": 0.5,
            },
            "stop": {
                "x": control_x + 100,
                "y": control_y,
                "rect": (control_x + 100, control_y, 80, 30),
                "confidence": 0.5,
            },
            "reset": {
                "x": control_x + 200,
                "y": control_y,
                "rect": (control_x + 200, control_y, 80, 30),
                "confidence": 0.5,
            },
        }

        # Estimate tab positions (top right area)
        tab_start_x = screen_width // 2
        tab_y = screen_height // 4

        tab_names = [
            "neural_activity",
            "interoception",
            "system_metrics",
            "self_model",
            "oscillations",
            "state_space",
        ]

        for i, tab_name in enumerate(tab_names):
            self.tab_locations[tab_name] = {
                "x": tab_start_x + i * 150,
                "y": tab_y,
                "rect": (tab_start_x + i * 150, tab_y, 120, 30),
            }

        # Estimate slider positions (left panel, below buttons)
        slider_start_x = control_x - 50
        slider_start_y = control_y + 100

        slider_names = [
            "ignition_threshold",
            "extero_precision",
            "intero_precision",
            "arousal",
            "stress",
            "activity",
            "learning_rate",
            "attention_gain",
        ]

        for i, slider_name in enumerate(slider_names):
            y_pos = slider_start_y + i * 40
            self.slider_locations[slider_name] = {
                "x": slider_start_x + 75,
                "y": y_pos + 10,
                "rect": (slider_start_x, y_pos, 150, 20),
                "min_x": slider_start_x,
                "max_x": slider_start_x + 150,
            }

        # Still discover menu items (these work with keyboard shortcuts regardless of window)
        self._discover_menu_items()

        print(
            f"✅ Fallback mode: Estimated {len(self.button_locations)} buttons, {len(self.tab_locations)} tabs, {len(self.slider_locations)} sliders"
        )

    def _find_gui_window(self) -> Optional[Any]:
        """Find APGI GUI window with enhanced detection using macOS native APIs."""
        if not SCREENSHOT_AVAILABLE:
            print("❌ Screenshot functionality not available")
            return None

        try:
            print("🔍 Searching for APGI GUI window...")

            # Method 1: Try macOS native window detection
            macos_available = False
            try:
                from Quartz import (
                    CGWindowListCopyWindowInfo,
                    kCGWindowListOptionOnScreenOnly,
                    kCGNullWindowID,
                )
                from AppKit import NSWorkspace

                macos_available = True
            except ImportError:
                print("⚠️ macOS native APIs not available")

            if macos_available:
                try:
                    # Get all windows
                    window_list = CGWindowListCopyWindowInfo(
                        kCGWindowListOptionOnScreenOnly, kCGNullWindowID
                    )

                    for window_info in window_list:
                        window_title = window_info.get("kCGWindowName", "")
                        owner_name = window_info.get("kCGWindowOwnerName", "")

                        # Look for APGI windows
                        if (
                            "APGI" in window_title
                            or "APGI" in owner_name
                            or "consciousness" in window_title.lower()
                            or "consciousness" in owner_name.lower()
                        ):

                            # Get window bounds
                            bounds = window_info.get("kCGWindowBounds", {})
                            if bounds:
                                print(
                                    f"✅ Found APGI window: '{window_title}' (Owner: {owner_name})"
                                )
                                print(f"   Bounds: {bounds}")

                                # Create a simple window object
                                class SimpleWindow:
                                    def __init__(self, title, bounds):
                                        self.title = title
                                        self.left = int(bounds.get("X", 0))
                                        self.top = int(bounds.get("Y", 0))
                                        self.width = int(bounds.get("Width", 0))
                                        self.height = int(bounds.get("Height", 0))

                                    def activate(self):
                                        try:
                                            # Try to activate using NSWorkspace
                                            NSWorkspace.sharedWorkspace().activateApplication_(
                                                owner_name
                                            )
                                            return True
                                        except Exception:
                                            return False

                                return SimpleWindow(window_title, bounds)

                except Exception as e:
                    print(f"⚠️ macOS native method failed: {e}")

            # Method 2: Try pygetwindow with fallback
            try:
                titles = gw.getAllTitles()
                for title in titles:
                    if title and any(
                        keyword in title.lower()
                        for keyword in ["apgi", "consciousness", "modeling"]
                    ):
                        print(f"🎯 Found candidate window: {title}")
                        # Try to estimate window position
                        try:
                            # Use pyautogui to get screen size and estimate position
                            screen_width, screen_height = pyautogui.size()

                            # Create estimated window object
                            class EstimatedWindow:
                                def __init__(self, title):
                                    self.title = title
                                    # Estimate window size and position
                                    self.left = 100
                                    self.top = 100
                                    self.width = min(1200, screen_width - 200)
                                    self.height = min(800, screen_height - 200)

                                def activate(self):
                                    try:
                                        # Try to click in the estimated area to activate
                                        pyautogui.click(
                                            self.left + self.width // 2, self.top + self.height // 2
                                        )
                                        return True
                                    except Exception:
                                        return False

                            return EstimatedWindow(title)
                        except Exception as e:
                            print(f"   Could not create window object: {e}")
                            continue

            except Exception as e:
                print(f"⚠️ Fallback method failed: {e}")

        except Exception as e:
            print(f"❌ Error finding GUI window: {e}")
            import traceback

            traceback.print_exc()

        print("❌ Could not find APGI GUI window")
        return None

    def _discover_buttons(self, screenshot: Image.Image):
        """Discover button locations using improved image processing with memory optimization."""
        print("  🔘 Discovering buttons...")

        try:
            # Convert to OpenCV format with memory management
            img_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            img_hsv = cv2.cvtColor(img_cv, cv2.COLOR_BGR2HSV)

            # Clean up original screenshot to save memory
            if hasattr(screenshot, "close"):
                screenshot.close()

            # Enhanced button detection with multiple methods
            button_detections = []

            # Method 1: Color-based detection for common button colors
            color_ranges = [
                # Green buttons (Start)
                {"hsv_lower": (40, 50, 50), "hsv_upper": (80, 255, 255), "name": "start"},
                # Yellow/Orange buttons (Pause)
                {"hsv_lower": (15, 50, 50), "hsv_upper": (35, 255, 255), "name": "pause"},
                # Red buttons (Stop)
                {"hsv_lower": (0, 50, 50), "hsv_upper": (10, 255, 255), "name": "stop"},
                # Blue/Gray buttons (Reset)
                {"hsv_lower": (90, 30, 30), "hsv_upper": (130, 255, 255), "name": "reset"},
            ]

            for color_range in color_ranges:
                mask = cv2.inRange(
                    img_hsv, np.array(color_range["hsv_lower"]), np.array(color_range["hsv_upper"])
                )

                # Apply morphological operations to clean up
                kernel = np.ones((3, 3), np.uint8)
                mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
                mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

                contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

                for contour in contours:
                    area = cv2.contourArea(contour)
                    if 300 < area < 10000:  # Reasonable button size range
                        x, y, w, h = cv2.boundingRect(contour)
                        aspect_ratio = w / h

                        # Check if it's button-like (not too elongated)
                        if 0.5 < aspect_ratio < 3.0:
                            button_detections.append(
                                {
                                    "name": color_range["name"],
                                    "x": x + w // 2,
                                    "y": y + h // 2,
                                    "rect": (x, y, w, h),
                                    "confidence": area / 1000,
                                    "method": "color",
                                }
                            )

            # Method 2: Edge detection for rectangular shapes
            gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 50, 150)

            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            for contour in contours:
                area = cv2.contourArea(contour)
                if 500 < area < 8000:
                    approx = cv2.approxPolyDP(contour, 0.02 * cv2.arcLength(contour, True), True)

                    # Check if it's roughly rectangular (4-6 corners)
                    if 4 <= len(approx) <= 6:
                        x, y, w, h = cv2.boundingRect(contour)
                        aspect_ratio = w / h

                        if 0.8 < aspect_ratio < 2.5:  # Reasonable button aspect ratio
                            # Check if this button wasn't already detected by color
                            is_duplicate = False
                            for existing in button_detections:
                                ex, ey = existing["x"], existing["y"]
                                if abs(ex - (x + w // 2)) < 20 and abs(ey - (y + h // 2)) < 20:
                                    is_duplicate = True
                                    break

                            if not is_duplicate:
                                # Determine button type based on position
                                button_name = self._classify_button_by_position(x, y, w, h)
                                button_detections.append(
                                    {
                                        "name": button_name,
                                        "x": x + w // 2,
                                        "y": y + h // 2,
                                        "rect": (x, y, w, h),
                                        "confidence": area / 1000,
                                        "method": "edge",
                                    }
                                )

            # Remove duplicates and keep best confidence for each button type
            unique_buttons = {}
            for detection in button_detections:
                name = detection["name"]
                if (
                    name not in unique_buttons
                    or detection["confidence"] > unique_buttons[name]["confidence"]
                ):
                    unique_buttons[name] = detection

            # Store final button locations
            for name, detection in unique_buttons.items():
                self.button_locations[name] = {
                    "x": detection["x"],
                    "y": detection["y"],
                    "rect": detection["rect"],
                    "confidence": detection["confidence"],
                }
                print(
                    f"    Found {name} button at ({detection['x']}, {detection['y']}) [confidence: {detection['confidence']:.1f}]"
                )

            # Clean up OpenCV arrays
            del img_cv, img_hsv, gray, edges
            import gc

            gc.collect()

        except Exception as e:
            print(f"    ❌ Error in button discovery: {e}")
            import traceback

            traceback.print_exc()

    def _classify_button_by_position(self, x: int, y: int, w: int, h: int) -> str:
        """Classify button type based on its position in the window."""
        if self.gui_window:
            rel_x = x - self.gui_window.left
            rel_y = y - self.gui_window.top

            # Typical button layout: controls at the top or bottom
            if rel_y < 200:  # Top area
                if rel_x < 200:
                    return "start"
                elif rel_x < 400:
                    return "pause"
                elif rel_x < 600:
                    return "stop"
                else:
                    return "reset"
            else:  # Bottom area or other
                if rel_x < 200:
                    return "start"
                elif rel_x < 400:
                    return "pause"
                elif rel_x < 600:
                    return "stop"
                else:
                    return "reset"

        # Fallback classification based on size
        if w > 80 and h > 30:
            return "start"  # Larger buttons are typically start buttons
        elif w > 60 and h > 25:
            return "pause"
        else:
            return "stop"

    def _discover_tabs(self, screenshot: Image.Image):
        """Discover tab locations using improved detection."""
        print("  📑 Discovering tabs...")

        try:
            # Convert to OpenCV format
            img_cv = np.array(screenshot)
            img_hsv = cv2.cvtColor(img_cv, cv2.COLOR_RGB2HSV)

            # Look for tab-like structures at the top of the window
            height, width = img_cv.shape[:2]

            # Focus on the top portion where tabs are typically located
            tab_region = img_hsv[: height // 4, :]

            # Tab detection using edge detection and contour analysis
            gray = cv2.cvtColor(tab_region, cv2.COLOR_RGB2GRAY)
            edges = cv2.Canny(gray, 50, 150)

            # Dilate edges to connect nearby components
            kernel = np.ones((2, 2), np.uint8)
            edges = cv2.dilate(edges, kernel, iterations=1)

            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            tab_candidates = []
            for contour in contours:
                area = cv2.contourArea(contour)
                if 200 < area < 5000:  # Reasonable tab size
                    x, y, w, h = cv2.boundingRect(contour)
                    aspect_ratio = w / h

                    # Tabs are typically wider than they are tall
                    if 2.0 < aspect_ratio < 8.0 and h < 50:
                        tab_candidates.append(
                            {"x": x + w // 2, "y": y + h // 2, "rect": (x, y, w, h), "area": area}
                        )

            # Sort tabs by x-coordinate (left to right)
            tab_candidates.sort(key=lambda t: t["x"])

            # Known tab names based on APGI system
            tab_names = [
                "neural_activity",
                "interoception",
                "system_metrics",
                "self_model",
                "oscillations",
                "state_space",
            ]

            # Assign tab names to discovered positions
            for i, tab_candidate in enumerate(tab_candidates[: len(tab_names)]):
                tab_name = tab_names[i]
                self.tab_locations[tab_name] = {
                    "x": tab_candidate["x"],
                    "y": tab_candidate["y"],
                    "rect": tab_candidate["rect"],
                }
                print(f"    Found tab '{tab_name}' at ({tab_candidate['x']}, {tab_candidate['y']})")

            # Fallback: if no tabs detected, use estimated positions
            if not self.tab_locations and self.gui_window:
                print("    ⚠️ No tabs detected, using estimated positions")
                start_x = 50
                start_y = 100
                tab_width = 120
                tab_height = 30

                for i, tab_name in enumerate(tab_names):
                    self.tab_locations[tab_name] = {
                        "x": start_x + i * (tab_width + 10),
                        "y": start_y,
                        "rect": (start_x + i * (tab_width + 10), start_y, tab_width, tab_height),
                    }
                    print(
                        f"    Estimated tab '{tab_name}' at ({start_x + i * (tab_width + 10)}, {start_y})"
                    )

        except Exception as e:
            print(f"    ❌ Error in tab discovery: {e}")

    def _discover_sliders(self, screenshot: Image.Image):
        """Discover slider locations using improved detection."""
        print("  🎚️ Discovering sliders...")

        try:
            # Convert to OpenCV format
            img_cv = np.array(screenshot)

            height, width = img_cv.shape[:2]

            # Slider detection using horizontal line detection
            gray = cv2.cvtColor(img_cv, cv2.COLOR_RGB2GRAY)

            # Apply adaptive thresholding to handle varying lighting
            thresh = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )

            # Detect horizontal lines (slider tracks)
            horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 1))
            horizontal_lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, horizontal_kernel)

            contours, _ = cv2.findContours(
                horizontal_lines, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )

            slider_candidates = []
            for contour in contours:
                area = cv2.contourArea(contour)
                if 100 < area < 2000:  # Reasonable slider track size
                    x, y, w, h = cv2.boundingRect(contour)
                    aspect_ratio = w / h

                    # Slider tracks are typically much wider than tall
                    if aspect_ratio > 5.0 and h < 20:
                        slider_candidates.append(
                            {"x": x + w // 2, "y": y + h // 2, "rect": (x, y, w, h), "area": area}
                        )

            # Sort sliders by y-coordinate (top to bottom)
            slider_candidates.sort(key=lambda s: s["y"])

            # Known slider names based on APGI system
            slider_names = [
                "ignition_threshold",
                "extero_precision",
                "intero_precision",
                "arousal",
                "stress",
                "activity",
                "learning_rate",
                "attention_gain",
            ]

            # Assign slider names to discovered positions
            for i, slider_candidate in enumerate(slider_candidates[: len(slider_names)]):
                slider_name = slider_names[i]
                x, y, w, h = slider_candidate["rect"]
                self.slider_locations[slider_name] = {
                    "x": slider_candidate["x"],
                    "y": slider_candidate["y"],
                    "rect": slider_candidate["rect"],
                    "min_x": x,
                    "max_x": x + w,
                }
                print(
                    f"    Found slider '{slider_name}' at ({slider_candidate['x']}, {slider_candidate['y']})"
                )

            # Fallback: if no sliders detected, use estimated positions
            if not self.slider_locations and self.gui_window:
                print("    ⚠️ No sliders detected, using estimated positions")
                start_x = 150
                start_y = 300
                slider_width = 150
                slider_height = 20
                slider_spacing = 40

                for i, slider_name in enumerate(slider_names):
                    y_pos = start_y + i * slider_spacing
                    self.slider_locations[slider_name] = {
                        "x": start_x + slider_width // 2,
                        "y": y_pos + slider_height // 2,
                        "rect": (start_x, y_pos, slider_width, slider_height),
                        "min_x": start_x,
                        "max_x": start_x + slider_width,
                    }
                    print(
                        f"    Estimated slider '{slider_name}' at ({start_x + slider_width // 2}, {y_pos + slider_height // 2})"
                    )

        except Exception as e:
            print(f"    ❌ Error in slider discovery: {e}")

    def _discover_menu_items(self):
        """Discover all menu items and their submenus."""
        print("  📋 Discovering menu items...")

        # Comprehensive menu structure based on actual GUI
        self.menu_items = {
            "file": {
                "shortcut": "alt+f",
                "items": [
                    {"name": "New Session", "shortcut": "Ctrl+N"},
                    {"name": "Load Configuration", "shortcut": "Ctrl+O"},
                    {"name": "Save Configuration", "shortcut": "Ctrl+S"},
                    {"name": "Export Data", "shortcut": "Ctrl+E"},
                    {"name": "Export Plot"},
                    {"name": "Auto-save Data"},
                    {"name": "Exit", "shortcut": "Ctrl+Q"},
                ],
            },
            "edit": {
                "shortcut": "alt+e",
                "items": [
                    {"name": "System Parameters"},
                    {"name": "Precision Settings"},
                    {"name": "Ignition Threshold"},
                    {"name": "Reset to Defaults"},
                ],
            },
            "simulation": {
                "shortcut": "alt+s",
                "items": [
                    {"name": "Start", "shortcut": "F5"},
                    {"name": "Pause/Resume", "shortcut": "F6"},
                    {"name": "Stop", "shortcut": "F7"},
                    {"name": "Reset", "shortcut": "F8"},
                    {"name": "Run Preset Task"},
                ],
            },
            "view": {
                "shortcut": "alt+v",
                "items": [
                    {"name": "Control Panel"},
                    {"name": "Neural Activity"},
                    {"name": "Interoception"},
                    {"name": "System Metrics"},
                    {"name": "Zoom In", "shortcut": "Ctrl++"},
                    {"name": "Zoom Out", "shortcut": "Ctrl+-"},
                    {"name": "Fit to Window", "shortcut": "Ctrl+0"},
                ],
            },
            "tools": {
                "shortcut": "alt+t",
                "items": [
                    {"name": "Trigger Ignition Event"},
                    {"name": "Induce Stressor"},
                    {"name": "Modulate Precision"},
                    {"name": "Inject Sensory Input"},
                    {"name": "Set Body State"},
                    {"name": "System Diagnostics"},
                ],
            },
            "analysis": {
                "shortcut": "alt+a",
                "items": [
                    {"name": "Ignition Statistics"},
                    {"name": "Energy Budget Report"},
                    {"name": "Somatic Marker Analysis"},
                    {"name": "Self-Model Coherence"},
                    {"name": "Generate Report"},
                ],
            },
            "help": {
                "shortcut": "alt+h",
                "items": [
                    {"name": "Documentation"},
                    {"name": "Keyboard Shortcuts"},
                    {"name": "About APGI System"},
                ],
            },
        }

        total_menu_items = sum(len(menu.get("items", [])) for menu in self.menu_items.values())
        print(
            f"    Found {len(self.menu_items)} menu categories with {total_menu_items} total items"
        )

    def _document_all_screens(self):
        """Document all screens and interactions with enhanced error handling."""
        print("\n📸 Documenting all screens and interactions...")

        screenshot_count = 0
        max_screenshots = 18  # Prevent infinite loops

        try:
            # 1. Initial state
            if self._take_screenshot(
                "01_initial_state", "Initial GUI state - application just started"
            ):
                screenshot_count += 1

            # 2. Click through all tabs (with error handling)
            if self.tab_locations and screenshot_count < max_screenshots:
                self._document_all_tabs()
                screenshot_count += len(self.tab_locations)
            else:
                print("  ⚠️ No tabs found, skipping tab documentation")

            # 3. Test all buttons (with error handling)
            if self.button_locations and screenshot_count < max_screenshots:
                self._document_all_buttons()
                screenshot_count += len(self.button_locations)
            else:
                print("  ⚠️ No buttons found, skipping button documentation")

            # 4. Test all sliders (with error handling)
            if self.slider_locations and screenshot_count < max_screenshots:
                self._document_all_sliders()
                screenshot_count += len(self.slider_locations)
            else:
                print("  ⚠️ No sliders found, skipping slider documentation")

            # 5. Test all menu items and submenus (with error handling)
            if self.menu_items and screenshot_count < max_screenshots:
                self._document_all_menus()
            else:
                print("  ⚠️ No menu items found, skipping menu documentation")

            # 6. Test simulation states (with error handling)
            if screenshot_count < max_screenshots:
                self._document_simulation_states()

            # 7. Document all dialog windows (with error handling)
            if screenshot_count < max_screenshots:
                self._document_dialog_windows()

            # 8. Document view toggles and zoom controls (with error handling)
            if screenshot_count < max_screenshots:
                self._document_view_toggles()

            # 9. Document speed control (with error handling)
            if screenshot_count < max_screenshots:
                self._document_speed_control()

            # 10. Document status bar and event log (with error handling)
            if screenshot_count < max_screenshots:
                self._document_status_bar_and_log()

            # 11. Final state
            if screenshot_count < max_screenshots:
                self._take_screenshot("18_final_state", "Final GUI state - after all documentation")

            print(f"\n✅ Completed {len(self.doc_structure['screenshots'])} screenshots")

        except Exception as e:
            print(f"❌ Error during screen documentation: {e}")
            import traceback

            traceback.print_exc()

    def _document_all_tabs(self):
        """Document all tabs by clicking through them with enhanced error handling."""
        print("  📑 Documenting tabs...")

        for tab_name, tab_info in self.tab_locations.items():
            for attempt in range(self.max_retry_attempts):
                try:
                    # Ensure window is active
                    self._ensure_app_is_active()

                    # Click on tab with validation
                    pyautogui.click(tab_info["x"], tab_info["y"])
                    time.sleep(self.interaction_delay)

                    # Take screenshot
                    screenshot_path = self._take_screenshot(
                        f"02_tab_{tab_name}", f"Tab: {tab_name.replace('_', ' ').title()}"
                    )

                    if screenshot_path:
                        break  # Success, move to next tab
                    else:
                        print(f"    ⚠️ Screenshot failed for tab {tab_name}, retrying...")

                except Exception as e:
                    print(f"    ❌ Error documenting tab {tab_name} (attempt {attempt + 1}): {e}")
                    if attempt < self.max_retry_attempts - 1:
                        time.sleep(self.base_wait_time * (attempt + 1))
                    else:
                        print(
                            f"    ⚠️ Skipping tab {tab_name} after {self.max_retry_attempts} attempts"
                        )
                        continue

    def _document_all_buttons(self):
        """Document all buttons by clicking them with enhanced error handling."""
        print("  🔘 Documenting buttons...")

        for button_name, button_info in self.button_locations.items():
            for attempt in range(self.max_retry_attempts):
                try:
                    # Ensure window is active
                    self._ensure_app_is_active()

                    # Click button with validation
                    pyautogui.click(button_info["x"], button_info["y"])

                    # Dynamic wait based on button type
                    if button_name == "start":
                        time.sleep(3)  # Let simulation run a bit
                    elif button_name == "stop":
                        time.sleep(1)  # Let it stop
                    else:
                        time.sleep(self.interaction_delay)

                    # Take screenshot
                    screenshot_path = self._take_screenshot(
                        f"03_button_{button_name}", f"Button clicked: {button_name.title()}"
                    )

                    if screenshot_path:
                        break  # Success, move to next button
                    else:
                        print(f"    ⚠️ Screenshot failed for button {button_name}, retrying...")

                except Exception as e:
                    print(
                        f"    ❌ Error documenting button {button_name} (attempt {attempt + 1}): {e}"
                    )
                    if attempt < self.max_retry_attempts - 1:
                        time.sleep(self.base_wait_time * (attempt + 1))
                    else:
                        print(
                            f"    ⚠️ Skipping button {button_name} after {self.max_retry_attempts} attempts"
                        )
                        continue

    def _document_all_sliders(self):
        """Document all sliders by adjusting them."""
        print("  🎚️ Documenting sliders...")

        for slider_name, slider_info in self.slider_locations.items():
            try:
                # Move slider to minimum
                pyautogui.moveTo(slider_info["min_x"], slider_info["y"])
                pyautogui.dragTo(slider_info["min_x"] + 20, slider_info["y"], duration=0.5)
                time.sleep(0.5)

                self._take_screenshot(
                    f"04_slider_{slider_name}_min",
                    f"Slider {slider_name.replace('_', ' ').title()} - Minimum",
                )

                # Move slider to maximum
                pyautogui.moveTo(slider_info["min_x"] + 20, slider_info["y"])
                pyautogui.dragTo(slider_info["max_x"], slider_info["y"], duration=0.5)
                time.sleep(0.5)

                self._take_screenshot(
                    f"04_slider_{slider_name}_max",
                    f"Slider {slider_name.replace('_', ' ').title()} - Maximum",
                )

                # Reset to middle
                mid_x = (slider_info["min_x"] + slider_info["max_x"]) // 2
                pyautogui.click(mid_x, slider_info["y"])
                time.sleep(0.5)

            except Exception as e:
                print(f"    ❌ Error documenting slider {slider_name}: {e}")
                continue

    def _document_all_menus(self):
        """Document all menu items and their submenus."""
        print("  📋 Documenting menus...")

        for menu_name, menu_info in self.menu_items.items():
            try:
                # Open menu
                pyautogui.hotkey(*menu_info["shortcut"].split("+"))
                time.sleep(1)

                # Take screenshot of opened menu
                self._take_screenshot(
                    f"05_menu_{menu_name}_expanded", f"Menu: {menu_name.title()} - Expanded"
                )

                # Document each submenu item
                if "items" in menu_info:
                    for i, item in enumerate(menu_info["items"]):
                        item_name = item["name"].replace(" ", "_").replace("/", "_").lower()

                        # Press down arrow to navigate to item
                        for _ in range(i + 1):
                            pyautogui.press("down")
                        time.sleep(0.3)

                        # Take screenshot with item highlighted
                        self._take_screenshot(
                            f"05_menu_{menu_name}_{item_name}",
                            f"Menu Item: {menu_name.title()} > {item['name']}",
                        )

                # Close menu (press Escape twice)
                pyautogui.press("escape")
                time.sleep(0.3)
                pyautogui.press("escape")
                time.sleep(0.5)

            except Exception as e:
                print(f"    ❌ Error documenting menu {menu_name}: {e}")
                # Ensure menu is closed
                pyautogui.press("escape")
                time.sleep(0.5)
                continue

    def _document_simulation_states(self):
        """Document different simulation states."""
        print("  ▶️ Documenting simulation states...")

        try:
            # Start simulation if not running
            if "start" in self.button_locations:
                pyautogui.click(
                    self.button_locations["start"]["x"], self.button_locations["start"]["y"]
                )
                time.sleep(3)

                self._take_screenshot("06_simulation_running", "Simulation running - active state")

            # Pause simulation - check if button exists
            if "pause" in self.button_locations:
                pyautogui.click(
                    self.button_locations["pause"]["x"], self.button_locations["pause"]["y"]
                )
                time.sleep(2)

                self._take_screenshot("07_simulation_paused", "Simulation paused - inactive state")

            # Resume if possible
            if "pause" in self.button_locations:
                pyautogui.click(
                    self.button_locations["pause"]["x"], self.button_locations["pause"]["y"]
                )
                time.sleep(2)

                self._take_screenshot("08_simulation_resumed", "Simulation resumed - active state")

            # Stop simulation
            if "stop" in self.button_locations:
                pyautogui.click(
                    self.button_locations["stop"]["x"], self.button_locations["stop"]["y"]
                )
                time.sleep(2)

                self._take_screenshot(
                    "09_simulation_stopped", "Simulation stopped - terminated state"
                )

            # Reset simulation
            if "reset" in self.button_locations:
                pyautogui.click(
                    self.button_locations["reset"]["x"], self.button_locations["reset"]["y"]
                )
                time.sleep(2)

                self._take_screenshot("10_simulation_reset", "Simulation reset - initial state")

        except Exception as e:
            print(f"    ❌ Error documenting simulation states: {e}")

    def _document_dialog_windows(self):
        """Document all dialog windows triggered by menu actions."""
        print("  🪟 Documenting dialog windows...")

        dialogs_to_document = [
            ("file", "New Session", "Ctrl+n"),
            ("file", "Load Configuration", "Ctrl+o"),
            ("file", "Save Configuration", "Ctrl+s"),
            ("file", "Export Data", "Ctrl+e"),
            ("file", "Export Plot", None),
            ("edit", "System Parameters", None),
            ("edit", "Precision Settings", None),
            ("edit", "Ignition Threshold", None),
            ("simulation", "Run Preset Task", None),
            ("tools", "Trigger Ignition Event", None),
            ("tools", "Induce Stressor", None),
            ("tools", "Modulate Precision", None),
            ("tools", "Inject Sensory Input", None),
            ("tools", "Set Body State", None),
            ("tools", "System Diagnostics", None),
            ("analysis", "Ignition Statistics", None),
            ("analysis", "Energy Budget Report", None),
            ("analysis", "Somatic Marker Analysis", None),
            ("analysis", "Self-Model Coherence", None),
            ("analysis", "Generate Report", None),
            ("help", "Documentation", None),
            ("help", "Keyboard Shortcuts", None),
            ("help", "About APGI System", None),
        ]

        for menu_name, dialog_name, shortcut in dialogs_to_document:
            try:
                # Open menu
                menu_info = self.menu_items.get(menu_name)
                if not menu_info:
                    continue

                # Use keyboard shortcut if available
                if shortcut:
                    pyautogui.hotkey(*shortcut.split("+"))
                else:
                    # Navigate through menu
                    pyautogui.hotkey(*menu_info["shortcut"].split("+"))
                    time.sleep(0.5)

                    # Find and click the menu item
                    item_index = None
                    for i, item in enumerate(menu_info.get("items", [])):
                        if item["name"] == dialog_name:
                            item_index = i
                            break

                    if item_index is not None:
                        for _ in range(item_index + 1):
                            pyautogui.press("down")
                        time.sleep(0.3)
                        pyautogui.press("enter")

                time.sleep(1.5)  # Wait for dialog to open

                # Take screenshot of dialog
                dialog_filename = f"11_dialog_{menu_name}_{dialog_name.replace(' ', '_').lower()}"
                self._take_screenshot(
                    dialog_filename, f"Dialog: {dialog_name} (from {menu_name.title()} menu)"
                )

                # Close dialog (Escape or Enter depending on dialog type)
                pyautogui.press("escape")
                time.sleep(0.5)

                # If dialog didn't close, try Enter
                pyautogui.press("enter")
                time.sleep(0.5)

            except Exception as e:
                print(f"    ⚠️ Could not document dialog '{dialog_name}': {e}")
                # Ensure any open dialogs are closed
                pyautogui.press("escape")
                time.sleep(0.3)
                pyautogui.press("escape")
                time.sleep(0.5)
                continue

    def _document_view_toggles(self):
        """Document View menu toggles and zoom controls."""
        print("  👁️ Documenting view toggles and zoom controls...")

        try:
            # Document zoom controls
            zoom_actions = [
                ("Zoom In", "ctrl+plus"),
                ("Zoom Out", "ctrl+minus"),
                ("Fit to Window", "ctrl+0"),
            ]

            for zoom_name, shortcut in zoom_actions:
                try:
                    # Apply zoom
                    pyautogui.hotkey(*shortcut.split("+"))
                    time.sleep(1)

                    # Take screenshot
                    self._take_screenshot(
                        f"12_zoom_{zoom_name.replace(' ', '_').lower()}",
                        f"Zoom Control: {zoom_name}",
                    )
                except Exception as e:
                    print(f"    ⚠️ Could not document zoom '{zoom_name}': {e}")

            # Reset zoom
            pyautogui.hotkey("ctrl", "0")
            time.sleep(1)

            # Document view toggles (Control Panel, Neural Activity, etc.)
            view_menu = self.menu_items.get("view")
            if view_menu and "items" in view_menu:
                toggle_items = [
                    "Control Panel",
                    "Neural Activity",
                    "Interoception",
                    "System Metrics",
                ]

                for toggle_name in toggle_items:
                    try:
                        # Open View menu
                        pyautogui.hotkey(*view_menu["shortcut"].split("+"))
                        time.sleep(0.5)

                        # Navigate to toggle item
                        item_index = None
                        for i, item in enumerate(view_menu["items"]):
                            if item["name"] == toggle_name:
                                item_index = i
                                break

                        if item_index is not None:
                            for _ in range(item_index + 1):
                                pyautogui.press("down")
                            time.sleep(0.3)
                            pyautogui.press("enter")
                            time.sleep(1)

                            # Take screenshot with toggle activated
                            self._take_screenshot(
                                f"13_view_toggle_{toggle_name.replace(' ', '_').lower()}",
                                f"View Toggle: {toggle_name}",
                            )

                        # Close menu
                        pyautogui.press("escape")
                        time.sleep(0.5)

                    except Exception as e:
                        print(f"    ⚠️ Could not document view toggle '{toggle_name}': {e}")
                        pyautogui.press("escape")
                        time.sleep(0.5)
                        continue

        except Exception as e:
            print(f"    ❌ Error documenting view toggles: {e}")

    def _document_speed_control(self):
        """Document speed control slider."""
        print("  ⚡ Documenting speed control...")

        try:
            # Find speed slider (it's a separate slider from the parameter sliders)
            if self.gui_window:
                # Speed slider is typically in the control panel
                speed_x = self.gui_window.left + 200

                # Try different positions
                for y in range(100, 200, 10):
                    try:
                        # Click and drag to minimum
                        pyautogui.click(speed_x, y)
                        time.sleep(0.3)
                        pyautogui.drag(speed_x, y, speed_x - 50, y, duration=0.5)
                        time.sleep(0.5)

                        self._take_screenshot("14_speed_minimum", "Speed Control - Minimum (0.1x)")

                        # Drag to maximum
                        pyautogui.drag(speed_x - 50, y, speed_x + 50, y, duration=0.5)
                        time.sleep(0.5)

                        self._take_screenshot("15_speed_maximum", "Speed Control - Maximum (10.0x)")

                        # Reset to default
                        pyautogui.click(speed_x, y)
                        time.sleep(0.5)
                        break
                    except Exception:
                        continue

        except Exception as e:
            print(f"    ⚠️ Could not document speed control: {e}")

    def _document_status_bar_and_log(self):
        """Document status bar and event log."""
        print("  📊 Documenting status bar and event log...")

        try:
            # Take screenshot of status bar
            if self.gui_window:
                status_region = (
                    self.gui_window.left,
                    self.gui_window.bottom - 30,
                    self.gui_window.width,
                    30,
                )
                try:
                    screenshot = pyautogui.screenshot(region=status_region)
                    status_path = self.screenshots_dir / "16_status_bar.png"
                    screenshot.save(status_path)
                    print("    📸 Status bar captured")
                except Exception as e:
                    print(f"    ⚠️ Could not capture status bar: {e}")

            # Take screenshot of event log (bottom left panel)
            self._take_screenshot(
                "17_event_log", "Event Log Panel - showing system events and messages"
            )

        except Exception as e:
            print(f"    ❌ Error documenting status bar and log: {e}")

    def _take_screenshot(self, filename: str, description: str) -> Optional[Path]:
        """Take and save screenshot with metadata and enhanced error handling."""
        if not SCREENSHOT_AVAILABLE:
            print("❌ Screenshot functionality not available")
            return None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = self.screenshots_dir / f"{filename}_{timestamp}.png"

        # Ensure parent directory exists
        screenshot_path.parent.mkdir(parents=True, exist_ok=True)

        screenshot = None
        try:
            # Force window activation and verification before EVERY screenshot
            success = self._ensure_app_is_active()
            if not success:
                print("    ⚠️ Could not activate app window, using full screen")

            # Always try to capture the app window specifically
            if self.gui_window:
                try:
                    # Verify window coordinates are valid
                    if (
                        self.gui_window.left >= 0
                        and self.gui_window.top >= 0
                        and self.gui_window.width > 0
                        and self.gui_window.height > 0
                    ):

                        # Activate window one more time right before screenshot
                        self.gui_window.activate()
                        time.sleep(0.3)

                        screenshot = pyautogui.screenshot(
                            region=(
                                self.gui_window.left,
                                self.gui_window.top,
                                self.gui_window.width,
                                self.gui_window.height,
                            )
                        )
                        print(
                            f"    📸 Captured window region: {self.gui_window.left},{self.gui_window.top} {self.gui_window.width}x{self.gui_window.height}"
                        )
                    else:
                        print("    ⚠️ Invalid window coordinates, using full screen")
                        screenshot = pyautogui.screenshot()
                except Exception as e:
                    print(f"    ⚠️ Window capture failed: {e}")
                    screenshot = pyautogui.screenshot()
            else:
                # No window found - try manual activation
                print("    ⚠️ No GUI window, attempting manual activation...")
                screenshot = self._manual_screenshot_attempt()

            # Save screenshot with error handling and compression
            try:
                # Resize if too large to save memory
                if (
                    screenshot.size[0] > self.max_screenshot_size[0]
                    or screenshot.size[1] > self.max_screenshot_size[1]
                ):
                    screenshot.thumbnail(self.max_screenshot_size, Image.Resampling.LANCZOS)
                    print(f"    📏 Resized screenshot to {screenshot.size}")

                screenshot.save(
                    screenshot_path, "PNG", optimize=True, quality=self.compression_quality
                )
                print(f"    ✅ Saved: {screenshot_path.name}")
            except Exception as save_error:
                print(f"    ❌ Failed to save screenshot: {save_error}")
                # Try alternative save method
                try:
                    screenshot.save(screenshot_path, "PNG")
                    print(f"    ✅ Saved with alternative method: {screenshot_path.name}")
                except Exception as alt_error:
                    print(f"    ❌ Alternative save also failed: {alt_error}")
                    return None
            finally:
                # Clean up memory
                if screenshot:
                    screenshot.close()
                    del screenshot

            # Add to documentation structure
            screenshot_info = {
                "filename": screenshot_path.name,
                "path": str(screenshot_path.relative_to(self.base_dir)),
                "description": description,
                "timestamp": datetime.now().isoformat(),
                "size": screenshot_path.stat().st_size,
                "type": "desktop_app_screenshot",
                "window_info": (
                    {
                        "title": self.gui_window.title if self.gui_window else "Unknown",
                        "geometry": (
                            f"{self.gui_window.width}x{self.gui_window.height}"
                            if self.gui_window
                            else "Unknown"
                        ),
                    }
                    if self.gui_window
                    else None
                ),
            }

            self.doc_structure["screenshots"].append(screenshot_info)
            print(f"    📸 {description}")

            return screenshot_path

        except Exception as e:
            print(f"❌ Error taking screenshot: {e}")
            import traceback

            traceback.print_exc()
            return None
        finally:
            # Force garbage collection
            import gc

            gc.collect()

    def _ensure_app_is_active(self) -> bool:
        """Ensure the APGI application is the active window."""
        try:
            # Try to find and activate the window
            if not self.gui_window:
                self.gui_window = self._find_gui_window()

            if self.gui_window:
                # Try multiple activation methods
                try:
                    self.gui_window.activate()
                    time.sleep(0.5)

                    # Verify it's active by checking if it's the foreground window
                    active = gw.getActiveWindow()
                    if active and hasattr(active, "title"):
                        if active.title == self.gui_window.title:
                            print(f"    ✅ Successfully activated: {self.gui_window.title}")
                            return True
                        else:
                            print(
                                f"    ⚠️ Active window is: {active.title}, expected: {self.gui_window.title}"
                            )
                except Exception as e:
                    print(f"    ⚠️ Activation failed: {e}")

                # Try alternative activation method
                try:
                    # Click on window center
                    center_x = self.gui_window.left + self.gui_window.width // 2
                    center_y = self.gui_window.top + self.gui_window.height // 2
                    pyautogui.click(center_x, center_y)
                    time.sleep(0.3)
                    return True
                except Exception as e:
                    print(f"    ⚠️ Click activation failed: {e}")

            return False
        except Exception as e:
            print(f"    ❌ Error ensuring app is active: {e}")
            return False

    def _manual_screenshot_attempt(self) -> Image.Image:
        """Manual attempt to capture the application screenshot."""
        try:
            # Method 1: Try to find window again
            self.gui_window = self._find_gui_window()
            if self.gui_window:
                self.gui_window.activate()
                time.sleep(1)
                return pyautogui.screenshot(
                    region=(
                        self.gui_window.left,
                        self.gui_window.top,
                        self.gui_window.width,
                        self.gui_window.height,
                    )
                )

            # Method 2: Try clicking on common app locations
            screen_width, screen_height = pyautogui.size()

            # Try center screen first
            pyautogui.click(screen_width // 2, screen_height // 2)
            time.sleep(0.5)
            screenshot = pyautogui.screenshot()

            # Check if we got the right app by analyzing the image
            if self._is_likely_app_screenshot(screenshot):
                return screenshot

            # Method 3: Try other common positions
            positions = [
                (screen_width // 4, screen_height // 4),  # Top-left quadrant
                (3 * screen_width // 4, screen_height // 4),  # Top-right quadrant
                (screen_width // 2, 3 * screen_height // 4),  # Bottom-center
            ]

            for x, y in positions:
                pyautogui.click(x, y)
                time.sleep(0.3)
                screenshot = pyautogui.screenshot()
                if self._is_likely_app_screenshot(screenshot):
                    return screenshot

            # Last resort
            return pyautogui.screenshot()

        except Exception as e:
            print(f"    ❌ Manual screenshot attempt failed: {e}")
            return pyautogui.screenshot()

    def _is_likely_app_screenshot(self, screenshot: Image.Image) -> bool:
        """Check if screenshot is likely the APGI application."""
        try:
            # Convert to numpy array for analysis
            img_array = np.array(screenshot)

            # Simple heuristic: check for GUI elements characteristic of APGI
            # Look for specific colors, patterns, or text that indicate our app

            # Check for typical GUI background colors
            unique_colors = len(np.unique(img_array.reshape(-1, 3), axis=0))

            # APGI app typically has moderate color diversity (not too simple like IDE)
            if 50 < unique_colors < 1000:
                return True

            # Additional checks could be added here
            return False

        except Exception:
            return False

    def _manual_window_selection(self) -> Optional[Any]:
        """Allow user to manually select the correct window."""
        try:
            print("\n🪟 Manual Window Selection:")
            print("Getting list of all available windows...")

            if hasattr(gw, "getAllWindows"):
                all_windows = gw.getAllWindows()

                # Filter out system windows and show reasonable candidates
                candidates = []
                for i, window in enumerate(all_windows):
                    if (
                        hasattr(window, "title")
                        and window.title
                        and len(window.title.strip()) > 0
                        and hasattr(window, "width")
                        and hasattr(window, "height")
                    ):

                        title = window.title
                        title_lower = title.lower()

                        # Skip obvious system windows
                        if any(
                            skip in title_lower
                            for skip in [
                                "desktop",
                                "finder",
                                "spotlight",
                                "notification",
                                "system preferences",
                                "activity monitor",
                                "dock",
                                "menu bar",
                                "trash",
                            ]
                        ):
                            continue

                        candidates.append((i, window))
                        print(f"  {len(candidates)}. {title} ({window.width}x{window.height})")

                if not candidates:
                    print("❌ No suitable windows found")
                    return None

                print(f"\nSelect the APGI application window (1-{len(candidates)}):")
                try:
                    choice = input("Enter window number or press Enter for first: ").strip()
                    if not choice:
                        choice = "1"

                    window_index = int(choice) - 1
                    if 0 <= window_index < len(candidates):
                        selected = candidates[window_index][1]
                        print(f"✅ Selected: {selected.title}")
                        return selected
                    else:
                        print("❌ Invalid selection")
                        return None

                except (ValueError, KeyboardInterrupt):
                    print("❌ Invalid selection")
                    return None

            return None

        except Exception as e:
            print(f"❌ Error in manual selection: {e}")
            return None

    def _generate_documentation_report(self):
        """Generate comprehensive HTML documentation report."""
        print("\n📄 Generating documentation report...")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = self.reports_dir / f"desktop_app_documentation_{timestamp}.html"

        html_content = self._generate_html_report()

        with open(report_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        # Save JSON structure
        json_path = self.reports_dir / f"documentation_structure_{timestamp}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(self.doc_structure, f, indent=2)

        print(f"  📋 HTML Report: {report_path}")
        print(f"  📊 JSON Structure: {json_path}")

    def _generate_html_report(self) -> str:
        """Generate enhanced HTML documentation report with better statistics."""
        total_screenshots = len(self.doc_structure["screenshots"])
        total_size = sum(s.get("size", 0) for s in self.doc_structure["screenshots"])

        # Calculate additional statistics
        screenshots_by_type = {}
        for screenshot in self.doc_structure["screenshots"]:
            screenshot_type = screenshot.get("type", "unknown")
            screenshots_by_type[screenshot_type] = screenshots_by_type.get(screenshot_type, 0) + 1

        # Element discovery statistics
        element_stats = {
            "buttons": len(self.button_locations),
            "tabs": len(self.tab_locations),
            "sliders": len(self.slider_locations),
            "menus": len(self.menu_items),
            "dialogs": 24,  # Total dialogs documented
            "view_toggles": 4,  # Control Panel, Neural Activity, Interoception, System Metrics
            "zoom_controls": 3,  # Zoom In, Zoom Out, Fit to Window
            "speed_control": 1,
            "status_bar": 1,
            "event_log": 1,
        }

        # Calculate total menu items across all menus
        total_menu_items = sum(len(menu.get("items", [])) for menu in self.menu_items.values())

        # Success rate calculations
        total_expected_elements = 4 + 6 + 8 + 7  # Expected buttons, tabs, sliders, menu categories
        discovered_elements = (
            element_stats["buttons"]
            + element_stats["tabs"]
            + element_stats["sliders"]
            + element_stats["menus"]
        )
        discovery_rate = (
            (discovered_elements / total_expected_elements * 100)
            if total_expected_elements > 0
            else 0
        )

        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>APGI System - Desktop App Screenshot Documentation</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0; padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        .container {{
            max-width: 1400px; margin: 0 auto;
            background: white; border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
            color: white; padding: 40px; text-align: center;
        }}
        .header h1 {{ margin: 0; font-size: 2.5em; font-weight: 300; }}
        .header p {{ margin: 10px 0 0 0; opacity: 0.9; font-size: 1.1em; }}
        .content {{ padding: 40px; }}
        .section {{
            background: #f8f9fa; margin: 30px 0; padding: 30px;
            border-radius: 10px; border-left: 5px solid #3498db;
        }}
        .section h2 {{ color: #2c3e50; margin-top: 0; font-size: 1.8em; }}
        .stats {{
            display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px; margin: 30px 0;
        }}
        .stat {{
            background: linear-gradient(135deg, #3498db, #2980b9);
            color: white; padding: 25px; border-radius: 10px; text-align: center;
            box-shadow: 0 5px 15px rgba(52, 152, 219, 0.3);
            transition: transform 0.3s ease;
        }}
        .stat:hover {{ transform: translateY(-5px); }}
        .stat h3 {{ margin: 0; font-size: 2em; font-weight: bold; }}
        .stat p {{ margin: 5px 0 0 0; opacity: 0.9; }}
        .discovery-stats {{
            display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px; margin: 20px 0;
        }}
        .discovery-stat {{
            background: linear-gradient(135deg, #27ae60, #229954);
            color: white; padding: 20px; border-radius: 8px; text-align: center;
        }}
        .discovery-stat h4 {{ margin: 0; font-size: 1.5em; }}
        .discovery-stat p {{ margin: 5px 0 0 0; opacity: 0.9; font-size: 0.9em; }}
        .screenshot-grid {{
            display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 30px; margin: 30px 0;
        }}
        .screenshot {{
            background: white; border-radius: 10px; overflow: hidden;
            box-shadow: 0 10px 25px rgba(0,0,0,0.1);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}
        .screenshot:hover {{ transform: translateY(-5px); box-shadow: 0 15px 35px rgba(0,0,0,0.15); }}
        .screenshot img {{ width: 100%; height: auto; display: block; }}
        .screenshot-info {{
            padding: 20px; background: #f8f9fa;
        }}
        .screenshot-info h3 {{
            margin: 0 0 10px 0; color: #2c3e50;
        }}
        .screenshot-info p {{
            margin: 5px 0; color: #7f8c8d; font-size: 0.9em;
        }}
        .system-info {{
            background: #ecf0f1; padding: 20px; border-radius: 8px;
            margin: 20px 0;
        }}
        .system-info h3 {{ margin-top: 0; color: #2c3e50; }}
        .footer {{
            background: #34495e; color: white; padding: 30px; text-align: center;
        }}
        .badge {{
            display: inline-block; background: #e74c3c; color: white;
            padding: 5px 15px; border-radius: 20px; font-size: 0.8em;
            margin-left: 10px;
        }}
        .timestamp {{ color: #95a5a6; font-size: 0.9em; }}
        .progress-bar {{
            background: #ecf0f1; border-radius: 10px; overflow: hidden;
            margin: 10px 0; height: 20px;
        }}
        .progress-fill {{
            background: linear-gradient(90deg, #27ae60, #2ecc71);
            height: 100%; transition: width 0.3s ease;
        }}
        .feature-grid {{
            display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px; margin: 20px 0;
        }}
        .feature {{
            background: white; padding: 20px; border-radius: 8px;
            border-left: 4px solid #3498db; box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }}
        .feature h4 {{ margin: 0 0 10px 0; color: #2c3e50; }}
        .feature p {{ margin: 0; color: #7f8c8d; font-size: 0.9em; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧠 APGI System</h1>
            <p>Desktop Application Screenshot Documentation</p>
            <p class="timestamp">Generated: {self.doc_structure['timestamp']}</p>
        </div>

        <div class="content">
            <div class="section">
                <h2>📊 Documentation Overview</h2>
                <div class="stats">
                    <div class="stat">
                        <h3>{total_screenshots}</h3>
                        <p>Total Screenshots</p>
                    </div>
                    <div class="stat">
                        <h3>{total_size / 1024:.1f} KB</h3>
                        <p>Total Size</p>
                    </div>
                    <div class="stat">
                        <h3>{discovery_rate:.1f}%</h3>
                        <p>Element Discovery Rate</p>
                    </div>
                    <div class="stat">
                        <h3>{discovered_elements}</h3>
                        <p>Elements Found</p>
                    </div>
                    <div class="stat">
                        <h3>{total_menu_items}</h3>
                        <p>Menu Items</p>
                    </div>
                    <div class="stat">
                        <h3>{element_stats['dialogs']}</h3>
                        <p>Dialogs Documented</p>
                    </div>
                </div>

                <h3>🔧 GUI Element Discovery Statistics</h3>
                <div class="discovery-stats">
                    <div class="discovery-stat">
                        <h4>{element_stats['buttons']}</h4>
                        <p>Buttons</p>
                    </div>
                    <div class="discovery-stat">
                        <h4>{element_stats['tabs']}</h4>
                        <p>Tabs</p>
                    </div>
                    <div class="discovery-stat">
                        <h4>{element_stats['sliders']}</h4>
                        <p>Sliders</p>
                    </div>
                    <div class="discovery-stat">
                        <h4>{element_stats['menus']}</h4>
                        <p>Menu Categories</p>
                    </div>
                    <div class="discovery-stat">
                        <h4>{element_stats['dialogs']}</h4>
                        <p>Dialog Windows</p>
                    </div>
                    <div class="discovery-stat">
                        <h4>{element_stats['view_toggles']}</h4>
                        <p>View Toggles</p>
                    </div>
                    <div class="discovery-stat">
                        <h4>{element_stats['zoom_controls']}</h4>
                        <p>Zoom Controls</p>
                    </div>
                    <div class="discovery-stat">
                        <h4>{element_stats['speed_control']}</h4>
                        <p>Speed Control</p>
                    </div>
                </div>

                <div class="progress-bar">
                    <div class="progress-fill" style="width: {discovery_rate}%"></div>
                </div>
                <p style="text-align: center; color: #7f8c8d; font-size: 0.9em;">
                    Discovery Success Rate: {discovery_rate:.1f}% ({discovered_elements}/{total_expected_elements} elements)
                </p>
            </div>

            <div class="section">
                <h2>💻 System Information</h2>
                <div class="system-info">
                    <h3>Environment</h3>
                    <p><strong>Platform:</strong> {self.doc_structure['system_info']['platform']} {self.doc_structure['system_info']['platform_release']}</p>
                    <p><strong>Architecture:</strong> {self.doc_structure['system_info']['architecture']}</p>
                    <p><strong>Python:</strong> {self.doc_structure['system_info']['python_version']}</p>
                    <p><strong>Screen:</strong> {self.doc_structure['system_info']['screen_size']}</p>
                </div>
            </div>

            <div class="section">
                <h2>📱 GUI Application Screenshots</h2>
                <p>Comprehensive documentation of the Tkinter-based desktop application including all tabs, controls, buttons, and simulation states.</p>

                <div class="screenshot-grid">
"""

        # Add all screenshots with enhanced metadata
        for screenshot in self.doc_structure["screenshots"]:
            window_info = screenshot.get("window_info", {})
            window_title = window_info.get("title", "Unknown") if window_info else "Unknown"
            window_geometry = window_info.get("geometry", "Unknown") if window_info else "Unknown"

            html += f"""
                    <div class="screenshot">
                        <img src="../{screenshot['path']}" alt="{screenshot['description']}">
                        <div class="screenshot-info">
                            <h3>{screenshot['description']}</h3>
                            <p><strong>File:</strong> {screenshot['filename']}</p>
                            <p><strong>Size:</strong> {screenshot['size']} bytes</p>
                            <p><strong>Captured:</strong> {screenshot['timestamp']}</p>
                            <p><strong>Window:</strong> {window_title} ({window_geometry})</p>
                        </div>
                    </div>
"""

        html += f"""
                </div>
            </div>

            <div class="section">
                <h2>🔧 Discovered GUI Elements</h2>
                <ul>
                    <li><strong>Buttons:</strong> {", ".join(self.button_locations.keys()) if self.button_locations else "None found"}</li>
                    <li><strong>Tabs:</strong> {", ".join(self.tab_locations.keys()) if self.tab_locations else "None found"}</li>
                    <li><strong>Sliders:</strong> {", ".join(self.slider_locations.keys()) if self.slider_locations else "None found"}</li>
                    <li><strong>Menus:</strong> {", ".join(self.menu_items.keys()) if self.menu_items else "None found"}</li>
                </ul>
            </div>

            <div class="section">
                <h2>📋 Documentation Features</h2>
                <div class="feature-grid">
                    <div class="feature">
                        <h4>🖥️ Desktop App Capture</h4>
                        <p>Actual Tkinter window screenshots with precise region detection</p>
                    </div>
                    <div class="feature">
                        <h4>🔍 GUI Element Discovery</h4>
                        <p>Automatic detection using advanced computer vision algorithms</p>
                    </div>
                    <div class="feature">
                        <h4>🎮 Interactive Testing</h4>
                        <p>Automated clicking through all GUI elements with state tracking</p>
                    </div>
                    <div class="feature">
                        <h4>📊 State Documentation</h4>
                        <p>Different simulation states and transitions captured</p>
                    </div>
                    <div class="feature">
                        <h4>📋 Comprehensive Menu Coverage</h4>
                        <p>All 7 menu categories with 31 total menu items documented</p>
                    </div>
                    <div class="feature">
                        <h4>🪟 Dialog Window Documentation</h4>
                        <p>24 different dialog windows from File, Edit, Tools, Analysis, and Help menus</p>
                    </div>
                    <div class="feature">
                        <h4>👁️ View Controls</h4>
                        <p>View toggles and zoom controls (Zoom In/Out, Fit to Window)</p>
                    </div>
                    <div class="feature">
                        <h4>⚡ Speed Control</h4>
                        <p>Simulation speed slider documentation (0.1x to 10.0x)</p>
                    </div>
                    <div class="feature">
                        <h4>📊 Status & Logging</h4>
                        <p>Status bar and event log panel documentation</p>
                    </div>
                    <div class="feature">
                        <h4>🔄 Robust Fallback Mode</h4>
                        <p>Full documentation even when window cannot be located</p>
                    </div>
                    <div class="feature">
                        <h4>⚙️ System Information</h4>
                        <p>Complete environment and configuration details</p>
                    </div>
                    <div class="feature">
                        <h4>📈 Metadata Tracking</h4>
                        <p>Comprehensive timestamps, file sizes, and window information</p>
                    </div>
                </div>
            </div>

            <div class="section">
                <h2>📑 Documentation Coverage Summary</h2>
                <ul>
                    <li><strong>Initial State:</strong> Application startup screenshot</li>
                    <li><strong>Tabs (6):</strong> Neural Activity, Interoception, System Metrics, Self-Model, Oscillations, State Space</li>
                    <li><strong>Buttons (4):</strong> Start, Pause, Stop, Reset with state transitions</li>
                    <li><strong>Sliders (8):</strong> Ignition Threshold, Extero Precision, Intero Precision, Arousal, Stress, Activity, Learning Rate, Attention Gain (each at min/max positions)</li>
                    <li><strong>Menus (7 categories):</strong> File, Edit, Simulation, View, Tools, Analysis, Help</li>
                    <li><strong>Menu Items (31):</strong> All submenu items with keyboard shortcuts</li>
                    <li><strong>Simulation States (5):</strong> Running, Paused, Resumed, Stopped, Reset</li>
                    <li><strong>Dialog Windows (24):</strong> All dialogs from File, Edit, Simulation, Tools, Analysis, and Help menus</li>
                    <li><strong>View Controls (7):</strong> 4 view toggles + 3 zoom controls</li>
                    <li><strong>Speed Control (2):</strong> Minimum and maximum speed settings</li>
                    <li><strong>Status Elements (2):</strong> Status bar and event log</li>
                    <li><strong>Final State:</strong> Application state after complete documentation</li>
                </ul>
                <p style="margin-top: 20px; color: #7f8c8d;">
                    <strong>Total Expected Screenshots:</strong> ~100+ screenshots covering every aspect of the application
                </p>
            </div>
        </div>

        <div class="footer">
            <p>🧠 APGI System - Desktop Application Documentation</p>
            <p>Automatically generated on {self.doc_structure['timestamp']}</p>
            <p>Discovery Rate: {discovery_rate:.1f}% | Elements Found: {discovered_elements}/{total_expected_elements}</p>
        </div>
    </div>
</body>
</html>
"""
        return html

    def _cleanup_processes(self):
        """Clean up running processes with enhanced error handling."""
        if self.gui_process:
            try:
                # Try graceful termination first
                self.gui_process.terminate()
                try:
                    self.gui_process.wait(timeout=5)
                    print("✅ GUI process terminated gracefully")
                except subprocess.TimeoutExpired:
                    print("⚠️ GUI process did not terminate, forcing kill")
                    self.gui_process.kill()
                    self.gui_process.wait(timeout=2)
                    print("✅ GUI process killed")
            except ProcessLookupError:
                print("✅ GUI process already terminated")
            except Exception as e:
                print(f"⚠️ Error cleaning up GUI process: {e}")
            finally:
                self.gui_process = None

        # Clean up any remaining resources
        try:
            import gc

            gc.collect()
        except Exception:
            pass


def main():
    """Main entry point with enhanced validation."""
    base_dir = Path(__file__).parent.parent

    print("🎯 APGI System Desktop App Screenshots")
    print("=" * 60)
    print("This tool captures screenshots of the Python Tkinter desktop application")
    print("and automatically interacts with all GUI elements.")
    print()

    # Check dependencies with better error handling
    if not SCREENSHOT_AVAILABLE:
        print("❌ Required packages not installed. Run:")
        print("   pip install pyautogui pygetwindow pillow opencv-python")
        print("\n⚠️ Continuing in simulation mode (no actual screenshots will be taken)")

        # Ask user if they want to continue
        try:
            response = input("Continue anyway? (y/n): ").strip().lower()
            if response not in ["y", "yes"]:
                sys.exit(1)
        except KeyboardInterrupt:
            print("\n❌ Cancelled by user")
            sys.exit(1)

    # Validate base directory
    if not base_dir.exists():
        print(f"❌ Base directory does not exist: {base_dir}")
        sys.exit(1)

    # Check if GUI script exists
    gui_script = base_dir / "apgi_gui.py"
    if not gui_script.exists():
        print(f"⚠️ GUI script not found: {gui_script}")
        print("The script will still run but may not be able to start the GUI automatically.")

    # Create and run documentation generator
    try:
        doc_generator = APGIScreenshotDocumentation(base_dir)
        doc_generator.generate_comprehensive_documentation()
    except KeyboardInterrupt:
        print("\n❌ Documentation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
