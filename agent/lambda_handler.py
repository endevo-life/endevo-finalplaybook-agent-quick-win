"""AWS Lambda entrypoint. Wraps the same FastAPI `app` from app.main in Mangum so
it runs behind API Gateway with zero code changes to the routes.

In the SAM template this module's `handler` is the Lambda Handler. Locally you
run uvicorn against app.main:app -- this file is only used in the cloud.
"""
from mangum import Mangum

from app.main import app

handler = Mangum(app)
