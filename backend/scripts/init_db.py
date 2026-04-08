"""
DB initialization script.
- Creates all tables via SQLAlchemy metadata
- Seeds a default admin user for development

Usage:
    python -m scripts.init_db
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import get_settings
from app.models.database import engine, Base, async_session
from app.models.models import User  # noqa: F401 — register models


async def create_tables():
    print(f"Connecting to: {get_settings().DATABASE_URL}")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("All tables created successfully.")


async def seed_data():
    async with async_session() as session:
        # Check if admin user already exists
        existing = await session.get(User, "admin")
        if existing:
            print("Seed data already exists, skipping.")
            return

        admin = User(
            id="admin",
            email="admin@company.com",
            name="Admin",
            department="QA",
        )
        session.add(admin)
        await session.commit()
        print("Seed data inserted: admin user created.")


async def main():
    await create_tables()
    await seed_data()
    await engine.dispose()
    print("DB initialization complete.")


if __name__ == "__main__":
    asyncio.run(main())
