import sys
import os
import asyncio
import httpx
from dotenv import load_dotenv

sys.path.append(os.getcwd())
load_dotenv(os.path.join(os.getcwd(), ".env"))

# We need a valid token to access admin routes. 
# For this test, we might struggle if we need a full login flow.
# However, let's assume we can test the API logic if we mock the dependency OR 
# more practically, we look at the backend code:
#   dependencies=[Depends(get_current_active_superuser)]
#
# Since we don't have an easy way to get a token without a full auth flow (which is complex to script quickly),
# we will verify the code integrity by ensuring the server can import the new routes and the functions exist.
#
# BUT, we can try to "unit test" the endpoint logic by defining a small script that 
# imports the router and checks the signature/logic conceptually? No, that's weak.
#
# Better: Let's create a script that uses the `TestClient` from `fastapi.testclient`.
# This allows us to bypass the network layer but still hit the app logic.
# We can override the dependency to force a superuser.
from fastapi.testclient import TestClient
from app.main import app
from app.utils import auth_deps
from app.models.user import User

# Mock User
mock_admin = User(id=1, email="admin@example.com", is_superuser=True, is_active=True)

async def override_get_current_active_superuser():
    return mock_admin

app.dependency_overrides[auth_deps.get_current_active_superuser] = override_get_current_active_superuser

# MOCK Celery Task to avoid Broker connection issues during API test
from unittest.mock import MagicMock
from app.workers import tasks
tasks.fetch_articles_job = MagicMock()
tasks.fetch_articles_job.delay.return_value = MagicMock(id="mock-job-id-123")

client = TestClient(app)

def test_job_apis():
    print("Testing Job APIs...")
    
    # 1. Trigger Job with Accept: application/json
    print("\n[TEST] POST /api/admin/jobs/trigger/fetch (JSON)")
    res = client.post("/api/admin/jobs/trigger/fetch", headers={"Accept": "application/json"})
    print(f"Status: {res.status_code}")
    print(f"Body: {res.json()}")
    
    if res.status_code == 200 and "job_id" in res.json():
        print("PASS: JSON trigger worked.")
    else:
        print("FAIL: JSON trigger failed.")

    # 2. Trigger Job without JSON header (Redirection)
    print("\n[TEST] POST /api/admin/jobs/trigger/fetch (HTML Form)")
    res = client.post("/api/admin/jobs/trigger/fetch", allow_redirects=False)
    print(f"Status: {res.status_code}")
    if res.status_code == 303:
        print("PASS: Redirect worked.")
    else:
        print(f"FAIL: Expected 303, got {res.status_code}")

    # 3. Get Job List
    print("\n[TEST] GET /api/admin/jobs/list")
    res = client.get("/api/admin/jobs/list")
    print(f"Status: {res.status_code}")
    if res.status_code == 200:
        jobs = res.json()
        print(f"PASS: Got job list. Count: {len(jobs)}")
        if len(jobs) > 0:
            print(f"First Job: {jobs[0]['id']} - {jobs[0]['status']}")
    else:
        print(f"FAIL: {res.text}")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    test_job_apis()
