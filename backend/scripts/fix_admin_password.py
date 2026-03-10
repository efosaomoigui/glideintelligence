"""Check and fix admin user password hash"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.database import get_db
from app.models.user import User
from app.utils.security import get_password_hash
from sqlalchemy import select

async def fix_admin_password():
    """Check admin password hash and recreate if corrupted"""
    async for db in get_db():
        result = await db.execute(select(User).where(User.email == "admin@example.com"))
        user = result.scalar_one_or_none()
        
        if not user:
            print("[FAIL] Admin user not found")
            return
        
        print(f"[OK] Found admin user: {user.email}")
        print(f"Current hash length: {len(user.hashed_password)} characters")
        print(f"Hash prefix: {user.hashed_password[:10]}...")
        
        # Check if hash looks valid (bcrypt hashes start with $2b$ and are ~60 chars)
        if not user.hashed_password.startswith("$2b$") or len(user.hashed_password) < 50:
            print("[WARN] Password hash looks corrupted")
        
        # Recreate the password hash with the fix
        print("\nRecreating password hash with 'admin123'...")
        new_hash = get_password_hash("admin123")
        print(f"New hash length: {len(new_hash)} characters")
        print(f"New hash prefix: {new_hash[:10]}...")
        
        # Update the user
        user.hashed_password = new_hash
        await db.commit()
        
        print("\n[OK] Password hash updated successfully!")
        print("Try logging in with: admin@example.com / admin123")

if __name__ == "__main__":
    asyncio.run(fix_admin_password())
