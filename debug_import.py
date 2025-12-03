import sys
import traceback

try:
    from tests.property import test_properties_api
    print("Import successful")
    print("Functions:", [x for x in dir(test_properties_api) if x.startswith('test_')])
except Exception as e:
    print("Import failed:")
    traceback.print_exc()
