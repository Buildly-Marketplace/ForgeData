"""Initialize database with all required tables."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine
from src.core.config import settings
from src.core.database import Base
from src.models.credentials import CloudCredential, DatabaseConnection, OnboardingStatus


async def init_all_tables():
    """Create all database tables."""
    
    # Use async SQLite for local state
    database_url = settings.DATABASE_URL
    if database_url.startswith("sqlite"):
        database_url = database_url.replace("sqlite://", "sqlite+aiosqlite://")
    
    print(f"Initializing database at: {database_url}")
    
    engine = create_async_engine(database_url, echo=True)
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    print("✓ All tables created successfully!")
    print("\nCreated tables:")
    print("  - connection_configs")
    print("  - etl_jobs")
    print("  - reports")
    print("  - cloud_credentials")
    print("  - database_connections")
    print("  - onboarding_status")
    
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(init_all_tables())
