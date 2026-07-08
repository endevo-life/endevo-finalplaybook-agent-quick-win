"""Force the in-memory store for the whole test suite BEFORE any app/store import.

Without this, a developer .env with STORE_BACKEND=dynamodb would make the tests
hit (and pollute) real AWS tables. Tests must be hermetic and offline.
"""
import os

os.environ["STORE_BACKEND"] = "memory"
# Also blank out the dynamodb prefix so an accidental dynamodb path can't resolve.
os.environ.pop("DDB_TABLE_PREFIX", None)
# Force local (in-process) auth so a developer .env with AUTH_BACKEND=cognito
# can't make the tests call real Cognito. load_dotenv() won't override these.
os.environ["AUTH_BACKEND"] = "local"
# Local auth must return the code in-band so tests can log in without an email
# provider, regardless of the developer .env's AUTH_RETURN_CODE (prod-safe=false).
os.environ["AUTH_RETURN_CODE"] = "true"
