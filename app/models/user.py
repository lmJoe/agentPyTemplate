from datetime import datetime

from sqlalchemy import (
  Boolean,
  Integer,
  String,
  DateTime,
  ForeignKey
)

# 使用 SQLAlchemy ORM 定义了一个用户表 users 的数据模型。Python 的 User 类会映射到数据库中的 users 表

from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base



class User(Base):
  #  __tablename__ = "users"  表名为users
  __tablename__ = "users"

  # 数据库字段：id
  # 类型：最大 64 字符的字符串
  # primary_key=True：主键，要求唯一且不能为空
  # 适合保存 UUID，例如 u_a1b2c3d4
  id:Mapped[str] = mapped_column(String(64), primary_key=True)

  # 用户名，最长 100 字符，不能为空。
  username:Mapped[str] = mapped_column(String(100),nullable=False)

  # 用户角色 设置 nullable=False，避免数据库中出现没有角色的用户,默认为user
  role:Mapped[str] = mapped_column(String(50), nullable=True,default="user")

  # 用户是否启用
  is_active:Mapped[bool] = mapped_column(Boolean,default=True,nullable=False)

  # 记录创建时间。新建 User 时，如果未手动传入 created_at，SQLAlchemy 会调用datetime.now()生成当前时间
  created_at:Mapped[datetime] = mapped_column(DateTime() ,default=datetime.now, nullable=False)