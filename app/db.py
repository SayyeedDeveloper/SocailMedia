import os
import uuid
from dotenv import load_dotenv
from sqlalchemy import Column, Text, String, DateTime, UUID
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

class Base(DeclarativeBase):
    pass

class Post(Base):
    __tablename__ = "posts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    caption = Column(Text)
    url = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    file_name = Column(String, nullable=False)
    origin_name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

engine = create_async_engine(DATABASE_URL, echo=True)  # Use create_async_engine
async_session_maker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def create_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_async_session():
    async with async_session_maker() as session:
        yield session
