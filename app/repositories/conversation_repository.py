import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation
from app.models.message import Message

from app.schemas.chat import ChatMessage,MessageRole
from app.schemas.conversation import ConversationCreateRequest

# “会话数据仓库”（Repository）：负责把聊天会话和消息保存、读取到 PostgreSQL。路由或业务服务不直接写 SQL，而是调用它的方法。
# Conversation、Message：SQLAlchemy 数据库模型，对应会话表和消息表。
# ChatMessage、ConversationCreateRequest：接口层的数据结构；前者表示一条聊天消息，后者表示创建会话的请求。
# db: AsyncSession：异步数据库会话，由外部传进来

# 类 ConversationResponsitory 负责管理会话和会话消息
class ConversationRepository:
  # 创建会话方法,接收
  # conversation_id：服务端生成的会话 ID
  # request：前端传来的创建会话请求，例如标题
  async def create(
      self, 
      db:AsyncSession,
      request:ConversationCreateRequest,
      user_id: str | None = None
  ) -> Conversation:
    # 构造会话基本信息
    conversation = Conversation(
      id = f"c_{uuid.uuid4().hex[:8]}",
      title = request.title,
      user_id=user_id
    )

    # 加入本次数据库操作
    db.add(conversation)

    # 提交事务
    await db.commit()

    # 从数据库重新取回最新数据
    await db.refresh(conversation)

    # 返回新建的会话资料
    return conversation


  # 查询某个会话的全部消息，并按创建时间正序排列，最后转换成接口使用的 ChatMessage 列表
  async def get_messages(
      self,
      db:AsyncSession,
      conversation_id:str
  ) -> list[ChatMessage]:
      stmt = (
        # 查询 Message 模型对应的消息表
        select(Message)

        # .where(...)：只筛选属于当前 conversation_id 的消息
        .where(Message.conversation_id == conversation_id)

        # .order_by(Message.created_at.asc())：按创建时间从早到晚排序，保证聊天记录按正常对话顺序返回
        .order_by(Message.created_at.asc())
      )

      result = await db.execute(stmt)
      messages = result.scalars().all()

      return [
        ChatMessage(
            role=MessageRole(message.role),
            content=message.content
        )
        for message in messages
      ]

  # 创建一条消息，逻辑类似。消息 ID 形如 m_ab12cd34，并关联到指定的 conversation_id。
  async def add_message(
        self,
        db:AsyncSession,
        conversation_id:str,
        role:str,
        content:str,
        model:str | None = None
  ) -> Message:
     message = Message(
        id=f"m_{uuid.uuid4().hex[:8]}",
        conversation_id=conversation_id,
        role=role,
        content=content,
        model=model
     )

     db.add(message)
     await db.commit()
     await db.refresh(message)

     return message
  

# 创建一个全局仓库实例，其他 service 可以直接导入并调用：
conversation_repository = ConversationRepository()
    
