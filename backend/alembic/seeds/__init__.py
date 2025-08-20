import os
import importlib.util

# Expose seed_0001 from the file named '0001_seed.py' so it can be imported as
# `from alembic.seeds import seed_0001` despite the filename starting with digits.

def _load_seed_module():
    file_path = os.path.join(os.path.dirname(__file__), "0001_seed.py")
    spec = importlib.util.spec_from_file_location("alembic.seeds._0001_seed", file_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module

seed_0001 = _load_seed_module().seed_0001
