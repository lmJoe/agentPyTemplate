# 数据库的依赖,用于在每次请求中创建数据库连接，并在请求结束后确保关闭连接


# AsyncGenerator 表示这是一个异步生成器函数：它会通过 yield 暂时返回一个值，后续还能继续执行清理逻辑
from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import AsyncSessionLocal

# MockDBSession 此处是一个模拟对象,不是真实数据库
class MockDBSession:

  # execute(sql)：模拟执行 SQL
  async def execute(self, sql:str) -> str:
    return f"执行sql:{sql},返回结果"

  # close()：模拟关闭数据库连接
  async def close(self):
    print("关闭数据库连接")


# 连接数据库
async def get_db_session() -> AsyncGenerator[MockDBSession,None]:
  # 先查询数据库
  async with AsyncSessionLocal() as session:
    try: 
      # yield session 会把 session 提供给fastapi接口使用,不加的话会出现不关闭数据库的问题
      yield session
    finally:

      await session.close()