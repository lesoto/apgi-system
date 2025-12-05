"""Quick validation test for Windows build script."""
from build.build_windows import WindowsBuilder, BuildError
import sys

builder = WindowsBuilder()

try:
    builder.validate_environment()
    print('✓ Environment validation passed')
    print(f'  Platform: {sys.platform}')
    print(f'  Python version: {sys.version_info.major}.{sys.version_info.minor}')
    print(f'  Entry point exists: {(builder.project_root / "apgi_gui.py").exists()}')
    print(f'  Spec file exists: {builder.spec_file.exists()}')
except BuildError as e:
    print(f'✗ Validation failed: {e}')
    sys.exit(1)

print('\n✓ All validation checks passed!')
