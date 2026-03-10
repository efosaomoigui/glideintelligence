import asyncio
import httpx
from app.utils.security import create_access_token
from datetime import timedelta
from app.config import settings

async def trigger_run_now():
    # 1. Generate Token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject="admin@example.com", expires_delta=access_token_expires
    )
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        # Trigger AI Analysis
        print("Triggering AI Analysis...")
        resp = await client.post("/api/admin/jobs/trigger/ai", headers=headers)
        print(f"AI Trigger: {resp.status_code} - {resp.text}")

        # Trigger Trends
        print("Triggering Trends...")
        resp = await client.post("/api/admin/jobs/trigger/trends", headers=headers)
        print(f"Trends Trigger: {resp.status_code} - {resp.text}")

if __name__ == "__main__":
    asyncio.run(trigger_run_now())
