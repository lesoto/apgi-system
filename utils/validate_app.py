"""
Validation script for APGI System
Tests core functionality without GUI
"""

import sys
import traceback


def test_imports() -> bool:
    """Test all required imports."""
    print("Testing imports...")
    try:
        import numpy  # noqa: F401
        import scipy  # noqa: F401
        import matplotlib  # noqa: F401
        import yaml  # noqa: F401
        import tkinter  # noqa: F401

        print("✓ All core dependencies imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False


def test_apgi_system() -> bool:
    """Test APGI system initialization."""
    print("\nTesting APGI System...")
    try:
        from apgi_system.system import APGISystem
        from apgi_system.platform_utils import get_resource_path

        APGISystem(config_path=str(get_resource_path("config/default.yaml")))
        print("✓ APGI System initialized successfully")
        return True
    except Exception as e:
        print(f"✗ APGI System error: {e}")
        traceback.print_exc()
        return False


def test_system_step() -> bool:
    """Test system step function."""
    print("\nTesting system step...")
    try:
        import numpy as np
        from apgi_system.system import APGISystem
        from apgi_system.platform_utils import get_resource_path

        system = APGISystem(config_path=str(get_resource_path("config/default.yaml")))
        extero_input = np.random.randn(256)
        state = system.step(extero_input)

        # Check that state has expected keys
        required_keys = [
            "time",
            "ignition",
            "workspace",
            "body",
            "allostasis",
            "precision",
            "metabolism",
            "self_model",
        ]
        missing_keys = [k for k in required_keys if k not in state]

        if missing_keys:
            print(f"✗ Missing keys in state: {missing_keys}")
            return False

        print("✓ System step executed successfully")
        print(f"  - Time: {state['time']:.2f} ms")
        print(f"  - Ignition occurred: {state['ignition']['ignition_occurred']}")
        print(f"  - Workspace broadcasting: {state['workspace']['is_broadcasting']}")
        return True
    except Exception as e:
        print(f"✗ System step error: {e}")
        traceback.print_exc()
        return False


def test_gui_imports() -> bool:
    """Test GUI-specific imports."""
    print("\nTesting GUI imports...")
    try:
        import tkinter as tk  # noqa: F401
        from tkinter import ttk  # noqa: F401
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg  # noqa: F401
        from matplotlib.figure import Figure  # noqa: F401

        print("✓ GUI dependencies imported successfully")
        return True
    except ImportError as e:
        print(f"✗ GUI import error: {e}")
        return False


def test_config_file() -> bool:
    """Test configuration file."""
    print("\nTesting configuration file...")
    try:
        import yaml  # noqa: F401
        from pathlib import Path  # noqa: F401
        from apgi_system.platform_utils import get_resource_path

        config_path = get_resource_path("config/default.yaml")
        if not config_path.exists():
            print(f"✗ Config file not found: {config_path}")
            return False

        with open(config_path, "r") as f:
            config = yaml.safe_load(f)

        required_sections = ["system", "hierarchy", "active_inference", "ignition", "interoception"]
        missing_sections = [s for s in required_sections if s not in config]

        if missing_sections:
            print(f"✗ Missing config sections: {missing_sections}")
            return False

        print("✓ Configuration file valid")
        print(f"  - System name: {config['system']['name']}")
        print(f"  - Timestep: {config['system']['timestep_ms']} ms")
        return True
    except Exception as e:
        print(f"✗ Config file error: {e}")
        traceback.print_exc()
        return False


def test_experimental_tasks() -> bool:
    """Test experimental task imports."""
    print("\nTesting experimental tasks...")
    try:
        from apgi_system.experiments.tasks import (  # noqa: F401
            AttentionalBlinkTask,
            ChangeBlindnessTask,
            BinocularRivalryTask,
            IowaGamblingTask,
            MaskingParadigmTask,
        )

        print("✓ All experimental tasks imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Task import error: {e}")
        traceback.print_exc()
        return False


def test_gui_launch() -> bool:
    """Test that GUI can be launched."""
    print("\nTesting GUI launch...")
    try:
        import tkinter as tk
        from apgi_gui import APGIGui

        # Create root window
        root = tk.Tk()

        # Create GUI instance
        APGIGui(root)

        print("✓ GUI window opened successfully!")
        print(f"  - Window title: {root.title()}")
        print(f"  - Window size: {root.geometry()}")

        # Close immediately
        root.after(100, root.quit)

        # Run main loop
        root.mainloop()

        print("✓ GUI closed successfully!")
        return True

    except Exception as e:
        print(f"✗ GUI launch failed: {e}")
        traceback.print_exc()
        return False


def main() -> None:
    """Run all validation tests."""
    print("=" * 60)
    print("APGI System Validation")
    print("=" * 60)

    tests = [
        test_imports,
        test_config_file,
        test_apgi_system,
        test_system_step,
        test_gui_imports,
        test_gui_launch,
        test_experimental_tasks,
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
            traceback.print_exc()
            results.append(False)

    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Tests passed: {passed}/{total}")

    if passed == total:
        print("\n✓ ALL TESTS PASSED - Application is ready to use!")
        print("\nTo launch the GUI, run:")
        print("  python run_gui.py")
        print("  or")
        print("  python apgi_gui.py")
        return 0
    else:
        print("\n✗ SOME TESTS FAILED - Please review errors above")
        return 1


if __name__ == "__main__":
    sys.exit(main())
