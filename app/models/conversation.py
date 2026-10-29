from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Conversation(Base):
    
    #  __tablename__ = "users"  表名为conversations
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    user_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="active")

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        nullable=False,
    )

    # 定义了 SQLAlchemy ORM 的“对象关系”，通常表示：一个 Conversation 会话拥有多条 Message 消息
    messages = relationship(
        "Message",

        # back_populates 表示双向关联, Message 模型中必须有对应关系:
        # conversation = relationship(
        #     "Conversation",
        #     back_populates="messages",
        # )
        # 这样可以双向访问
        # conversation.messages  # 从会话找全部消息
        # message.conversation   # 从消息找所属会话
        back_populates="conversation",

        # 表示级联操作规则
        # all：对会话进行保存、更新、删除等操作时，关联消息会跟随处理
        # delete-orphan：若某条消息不再属于任何会话，SQLAlchemy 会删除它
        cascade="all, delete-orphan",
    )