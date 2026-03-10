"""
Create or update admin user with admin@gmail.com / admin123
"""
import asyncio
from app.database import AsyncSessionLocal
from app.models.user import User
from sqlalchemy import select
from app.utils.security import get_password_hash

async def fix_admin():
    async with AsyncSessionLocal() as db:
        # Check if admin@gmail.com exists
        result = await db.execute(
            select(User).where(User.email == 'admin@gmail.com')
        )
        user = result.scalar_one_or_none()
        
        if user:
            # Update password
            user.hashed_password = get_password_hash('admin123')
            user.is_active = True
            user.is_superuser = True
            print(f"Updated existing user: {user.email}")
        else:
            # Check for username conflict
            username = "admin"
            existing_username = await db.execute(select(User).where(User.username == username))
            if existing_username.scalar_one_or_none():
                username = "admin_gmail"

            # Create new admin user
            user = User(
                email='admin@gmail.com',
                username=username,
                hashed_password=get_password_hash('admin123'),
                full_name='Admin User',
                is_active=True,
                is_superuser=True
            )
            db.add(user)
            print(f"Created new user: admin@gmail.com")
        
        await db.commit()
        await db.refresh(user)
        
        print(f"\n[OK] Admin user ready:")
        print(f"   Email: {user.email}")
        print(f"   Password: admin123")
        print(f"   Active: {user.is_active}")
        print(f"   Superuser: {user.is_superuser}")
        print(f"\nYou can now login at: http://localhost:8000/admin/login")

if __name__ == "__main__":
    asyncio.run(fix_admin())
