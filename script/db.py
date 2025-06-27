from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, Integer, VARCHAR, ForeignKey

from db.models import User, Folder, Base as BaseMain

# Создание асинхронного движока и фабрики сессий
engine = create_async_engine("sqlite+aiosqlite:///instance/sqlite.db", echo=True)
async_session = async_sessionmaker(engine, expire_on_commit=False)

async def async_create_table():
    async with engine.begin() as conn:
        await conn.run_sync(BaseMain.metadata.create_all)
