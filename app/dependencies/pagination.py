# 分页的类

from fastapi import Query


# 定义了一个可复用的“分页参数类”，用于从 URL Query 参数中读取 page 和 size，并自动计算数据库查询所需的 offset


class PaginationParams:
  def __init__(
      self,
      page: int = Query(default=1, ge=1, description="页码"),
      size: int = Query(default=20, ge=1, le=100, description="每页数量")
  ):
    self.page = page
    self.size = size

  # @property 是 Python 的装饰器，用于把一个方法伪装成“属性”来使用
  # 就是在调用时 使用pagination.offset 而不是 pagination.offset()
  # 之所以这样用是因为 offset 不是独立保存的数据，而是由 page 和 size 自动计算出来的派生值, 它适合以“字段”的形式读取，但内部实际需要计算,使用@property 更简洁 也更自然
  @property
  def offset(self) -> int:
    return (self.page - 1) * self.size