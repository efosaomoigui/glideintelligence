"""Test admin login endpoint"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.database import get_db
from app.models.user import User
from app.utils.security import verify_password
from sqlalchemy import select

async def test_login():
    """Test login with admin credentials"""
    test_email = "admin@example.com"
    test_password = "admin123"  # Common default password
    
    async for db in get_db():
        result = await db.execute(select(User).where(User.email == test_email))
        user = result.scalar_one_or_none()
        
        if not user:
            print(f"[FAIL] User {test_email} not found")
            return
        
        print(f"[OK] User found: {user.email}")
        print(f"  Superuser: {user.is_superuser}")
        print(f"  Active: {user.is_active}")
        print(f"  Hashed password: {user.hashed_password[:50]}...")
        
        # Test password
        print(f"\nTesting password: '{test_password}'")
        is_valid = verify_password(test_password, user.hashed_password)
        
        if is_valid:
            print("[OK] Password is correct!")
        else:
            print("[FAIL] Password is incorrect!")
            print("\nTrying common passwords:")
            for pwd in ["admin", "admin123", "password", "Admin123!", "changeme"]:
                if verify_password(pwd, user.hashed_password):
                    print(f"  [OK] Correct password: '{pwd}'")
                    return
            print("  None of the common passwords worked.")
            print("  You may need to reset the admin password.")

if __name__ == "__main__":
    asyncio.run(test_login())
