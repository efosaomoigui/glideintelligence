import asyncio
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.user import User
from app.utils.security import get_password_hash

async def ensure_admin_user():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.email == "admin@example.com"))
        user = result.scalar_one_or_none()
        
        if not user:
            print("Admin user not found. Creating one...")
            user = User(
                email="admin@example.com",
                hashed_password=get_password_hash("admin"),
                full_name="Admin User",
                is_active=True,
                is_superuser=True
            )
            db.add(user)
            await db.commit()
            print("Admin user created (password: admin).")
        else:
            print("Admin user exists.")
            # Ensure it is superuser
            if not user.is_superuser:
                user.is_superuser = True
                await db.commit()
                print("Promoted to superuser.")

if __name__ == "__main__":
    asyncio.run(ensure_admin_user())
