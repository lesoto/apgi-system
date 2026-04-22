"""Quick test of platform utilities."""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from apgi_simulation.platform_utils import (  # noqa: E402
    get_config_dir,
    get_data_dir,
    get_platform,
    get_resource_path,
    is_bundled,
)

print(f"Platform: {get_platform()}")
print(f"Bundled: {is_bundled()}")
print(f"Config dir: {get_config_dir()}")
print(f"Data dir: {get_data_dir()}")
print(f"Resource path (config): {get_resource_path('config/default.yaml')}")
print(f"Resource path exists: {get_resource_path('config/default.yaml').exists()}")
