from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from typing import AsyncGenerator

from .config import settings
from dotenv import load_dotenv
load_dotenv()
# Buat async engine ke database sesuai URL dari config
# Tambahkan connect_args={"check_same_thread": False} khusus untuk SQLite
async_engine = create_async_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False}, # <--- INI TAMBAHAN PENTING
    echo=True,  # Set ke False di production
)

# Buat session maker untuk membuat session database (TIDAK BERUBAH)
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False
)

# Base class untuk semua model ORM lo nanti (TIDAK BERUBAH)
Base = declarative_base()

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency untuk menyediakan database session per request.
    (TIDAK ADA PERUBAHAN DI FUNGSI INI)
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()