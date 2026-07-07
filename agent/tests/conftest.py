"""Force the in-memory store for the whole test suite BEFORE any app/store import.

Without this, a developer .env with STORE_BACKEND=dynamodb would make the tests
hit (and pollute) real AWS tables. Tests must be hermetic and offline.
"""
import os

os.environ["STORE_BACKEND"] = "memory"
# Also blank out the dynamodb prefix so an accidental dynamodb path can't resolve.
os.environ.pop("DDB_TABLE_PREFIX", None)
