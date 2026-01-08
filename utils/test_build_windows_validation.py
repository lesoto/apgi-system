"""Quick validation test for Windows build script."""

import sys

sys.path.insert(0, "build")

from build_windows import WindowsBuilder


def test_builder():
    """Test WindowsBuilder initialization and basic methods."""
    print("=" * 60)
    print("Testing WindowsBuilder")
    print("=" * 60)

    # Initialize builder
    builder = WindowsBuilder()
    print(f"✓ Builder initialized: {builder.app_name} v{builder.version}")

    # Test environment validation
    valid = builder.validate_environment()
    print(f"✓ Environment validation: {'PASSED' if valid else 'FAILED'}")

    # Test spec file generation
    success = builder.generate_spec_file(onefile=True, console=False)
    print(f"✓ Spec file generation: {'SUCCESS' if success else 'FAILED'}")

    # Check if spec file was created
    import os

    if os.path.exists("build/pyinstaller.spec"):
        print("✓ Spec file created at build/pyinstaller.spec")

        # Read and display first few lines
        with open("build/pyinstaller.spec", "r") as f:
            lines = f.readlines()[:10]
            print("\nFirst 10 lines of spec file:")
            for line in lines:
                print(f"  {line.rstrip()}")
    else:
        print("✗ Spec file not found")

    print("\n" + "=" * 60)
    print("All tests completed")
    print("=" * 60)


if __name__ == "__main__":
    test_builder()
