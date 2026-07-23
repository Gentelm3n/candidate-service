from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from src.config import config
import logging

logger = logging.getLogger(__name__)

Base = declarative_base()

engine = create_async_engine(
    config.DATABASE_URL,
    echo=True,
    future=True
)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def init_db():
    logger.info(f"Known tables: {Base.metadata.tables.keys()}")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def close_db():
    await engine.dispose()

async def get_session() -> AsyncSession:
    async with async_session_maker() as session:
        yield session
