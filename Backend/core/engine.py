from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from core.setting import settings

DATABASE_URL = settings.DATABASE_URL

Engine= create_async_engine(DATABASE_URL)
SessionLocal= async_sessionmaker(autocommit=False, autoflush=False, bind=Engine, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

async def get_db():
    async with SessionLocal() as session:
        yield session


