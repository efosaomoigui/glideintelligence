import asyncio
import httpx
from app.database import AsyncSessionLocal
from app.models.user import User
from app.utils.security import create_access_token
from datetime import timedelta

async def trigger_jobs():
    # 1. Login/Get Token (Mocking a superuser token for local test)
    # We can skip login if we mock the dependency or just create a token manually if we have the secret
    # But easier to just hit the endpoint if we can bypass auth or valid token.
    # Since we are in the backend dir, we can probably use app code to generate a token.

    from app.config import settings
    
    # Generate a superuser token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject="admin@example.com", expires_delta=access_token_expires
    )
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        # Trigger Trends
        print("Triggering Trends...")
        resp = await client.post("/api/admin/jobs/trigger/trends", headers=headers)
        print(f"Trends Trigger: {resp.status_code} - {resp.text}")
        
        # Trigger Video (will likely fail gracefully if no API key or no trending topics)
        print("Triggering Video...")
        resp = await client.post("/api/admin/jobs/trigger/video", headers=headers)
        print(f"Video Trigger: {resp.status_code} - {resp.text}")

if __name__ == "__main__":
    # We need to ensure we run this in an environment where app keys are loaded
    # simpler: just run it. 
    asyncio.run(trigger_jobs())
