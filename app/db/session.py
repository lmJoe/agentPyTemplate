from sqlalchemy.ext.asyncio import (
  AsyncSession,
  async_sessionmaker,
  create_async_engine
)
from app.core.config import settings

# 表示异步的数据库引擎
engine = create_async_engine(
  settings.database_url,
  echo=settings.debug,
  pool_pre_ping=True
)
  
# 异步的会话工厂
AsyncSessionLocal = async_sessionmaker(
  bind=engine,
  class_=AsyncSession,
  expire_on_commit=False
)