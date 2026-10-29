from sqlalchemy.orm import DeclarativeBase


# 定义了项目中所有 SQLAlchemy ORM 数据模型的“公共父类”
# Base 的主要作用：
# - 让 SQLAlchemy 识别 User 是一个 ORM 数据库模型；
# - 收集所有继承 Base 的表结构信息；
# - 提供统一的元数据对象：Base.metadata

class Base(DeclarativeBase):
    pass