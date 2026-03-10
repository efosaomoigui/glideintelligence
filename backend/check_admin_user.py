"""
Check admin user credentials in database
"""
import asyncio
from app.database import AsyncSessionLocal
from app.models.user import User
from sqlalchemy import select
from app.utils.security import verify_password

async def check_admin():
    async with AsyncSessionLocal() as db:
        # Look for admin user
        result = await db.execute(
            select(User).where(User.email == 'admin@gmail.com')
        )
        user = result.scalar_one_or_none()
        
        if not user:
            print("[ERROR] User 'admin@gmail.com' not found in database")
            print("\nLooking for other admin users...")
            result = await db.execute(select(User))
            all_users = result.scalars().all()
            print(f"\nFound {len(all_users)} users:")
            for u in all_users:
                print(f"  - {u.email} (superuser: {u.is_superuser}, active: {u.is_active})")
        else:
            print(f"[OK] User found: {user.email}")
            print(f"   Active: {user.is_active}")
            print(f"   Superuser: {user.is_superuser}")
            print(f"   Full name: {user.full_name}")
            
            # Test password
            is_valid = verify_password('admin123', user.hashed_password)
            print(f"\n   Password 'admin123' valid: {is_valid}")
            
            if not is_valid:
                print("\n[WARNING] Password does not match!")
                print("   The user exists but the password is incorrect.")

if __name__ == "__main__":
    asyncio.run(check_admin())
