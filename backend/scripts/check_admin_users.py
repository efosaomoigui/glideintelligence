"""Check if admin user exists"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.database import get_db
from app.models.user import User
from sqlalchemy import select

async def check_users():
    async for db in get_db():
        result = await db.execute(select(User))
        users = result.scalars().all()
        
        print(f"Total users in database: {len(users)}")
        if len(users) == 0:
            print("\n❌ NO USERS FOUND - Admin login will fail!")
            print("   Run: python scripts/create_admin_user.py")
        else:
            print("\nUsers:")
            for user in users:
                print(f"  - Email: {user.email}")
                print(f"    Superuser: {user.is_superuser}")
                print(f"    Active: {user.is_active}")
                print()

if __name__ == "__main__":
    asyncio.run(check_users())
