import asyncio
import os
import sys

# Add the current directory to sys.path
sys.path.append(os.getcwd())

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from app.config import settings as app_settings
from app.models import *
# Import passlib for password hashing if available, or just use a placeholder for now
try:
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    def get_password_hash(password):
        return pwd_context.hash(password)
except ImportError:
    # Fallback if passlib isn't installed (it should be)
    def get_password_hash(password):
        return f"hashed_{password}"

async def seed_data():
    print(f"Connecting to {app_settings.DATABASE_URL}...")
    engine = create_async_engine(app_settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        print("Seeding Verticals...")
        verticals = [
            {"name": "Business & Finance", "slug": "business", "icon": "briefcase", "color": "#1ca1f2", "display_order": 1},
            {"name": "Technology & AI", "slug": "technology", "icon": "cpu", "color": "#6c5ce7", "display_order": 2},
            {"name": "Politics & Policy", "slug": "politics", "icon": "landmark", "color": "#e17055", "display_order": 3},
            {"name": "Health & Science", "slug": "science", "icon": "activity", "color": "#00b894", "display_order": 4},
        ]
        
        for v_data in verticals:
            stmt = select(Vertical).where(Vertical.slug == v_data["slug"])
            result = await session.execute(stmt)
            obj = result.scalar_one_or_none()
            if not obj:
                session.add(Vertical(**v_data))
        
        print("Seeding Source Groups...")
        groups = [
            {"name": "Global Media", "description": "International Tier-1 Outlets", "color": "#2d3436", "display_order": 1},
            {"name": "Local Press", "description": "Regional & Local Coverage", "color": "#0984e3", "display_order": 2},
            {"name": "Industry Experts", "description": "Specialized Blogs & Analysis", "color": "#00cec9", "display_order": 3},
        ]
        
        for g_data in groups:
            stmt = select(SourceGroup).where(SourceGroup.name == g_data["name"])
            result = await session.execute(stmt)
            obj = result.scalar_one_or_none()
            if not obj:
                session.add(SourceGroup(**g_data))

        print("Seeding Impact Categories...")
        categories = [
            {"name": "Economic Impact", "slug": "economic", "icon": "trending-up", "display_order": 1},
            {"name": "Social Impact", "slug": "social", "icon": "users", "display_order": 2},
            {"name": "Political Stability", "slug": "political", "icon": "flag", "display_order": 3},
            {"name": "Security", "slug": "security", "icon": "shield", "display_order": 4},
        ]
        
        for c_data in categories:
            stmt = select(ImpactCategory).where(ImpactCategory.slug == c_data["slug"])
            result = await session.execute(stmt)
            obj = result.scalar_one_or_none()
            if not obj:
                session.add(ImpactCategory(**c_data))

        print("Seeding Test Users...")
        admin_email = "admin@example.com"
        stmt = select(User).where(User.email == admin_email)
        result = await session.execute(stmt)
        admin = result.scalar_one_or_none()
        
        if not admin:
            admin = User(
                email=admin_email,
                username="admin",
                full_name="System Admin",
                hashed_password=get_password_hash("admin123"),
                is_active=True,
                is_superuser=True,
                role="admin",
                reputation_score=1000,
                is_verified=True
            )
            session.add(admin)
            
        expert_email = "expert@example.com"
        stmt = select(User).where(User.email == expert_email)
        result = await session.execute(stmt)
        expert = result.scalar_one_or_none()
        
        if not expert:
            expert = User(
                email=expert_email,
                username="expert_analyst",
                full_name="Expert Analyst",
                hashed_password=get_password_hash("expert123"),
                is_active=True,
                role="expert",
                bio="Senior market analyst with 10 years experience.",
                reputation_score=500,
                is_verified=True,
                verification_type="professional"
            )
            session.add(expert)

        await session.commit()
        print("Seeding Complete!")

    await engine.dispose()

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(seed_data())
