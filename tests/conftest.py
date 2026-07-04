"""Shared pytest setup for the tests/ suite.

Every test_*.py file repeats the same two lines before it can `import
prosodic`:

    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from prosodic.imports import *

conftest.py is collected by pytest before any test module, so putting the
sys.path fix here means the repo root is importable regardless of which
directory pytest is invoked from, without every test file needing to set it
up itself. (The `from prosodic.imports import *` star-import still has to
stay in each test file — conftest.py can't inject names into another
module's namespace.)
"""
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
