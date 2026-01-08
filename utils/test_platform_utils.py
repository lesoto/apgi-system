"""Quick test of platform utilities."""

from apgi_system.platform_utils import (
    get_platform,
    is_bundled,
    get_resource_path,
    get_config_dir,
    get_data_dir,
)

print(f"Platform: {get_platform()}")
print(f"Bundled: {is_bundled()}")
print(f"Config dir: {get_config_dir()}")
print(f"Data dir: {get_data_dir()}")
print(f"Resource path (config): {get_resource_path('config/default.yaml')}")
print(f"Resource path exists: {get_resource_path('config/default.yaml').exists()}")
