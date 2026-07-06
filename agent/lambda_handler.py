"""AWS Lambda entrypoint. Wraps the same FastAPI `app` from api.py in Mangum so
it runs behind API Gateway with zero code changes to the routes.

In the SAM template this module's `handler` is the Lambda Handler. Locally you
still run uvicorn against api:app -- this file is only used in the cloud.
"""
from mangum import Mangum

from api import app

handler = Mangum(app)
