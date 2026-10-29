# 导入 datetime，用于记录会话创建和更新时间
from datetime import datetime
# 导入 Enum，用于定义固定范围的会话状态
from enum import Enum
# BaseModel：定义 Pydantic 数据模型；Field：设置字段校验规则和接口文档描述
from pydantic import BaseModel, Field
# 导入聊天消息模型，用于表示会话中的消息列表
from app.schemas.chat import ChatMessage

# 定义会话状态枚举，继承 str 后会以普通字符串形式返回 JSON
class ConversationStatus(str, Enum):
    ACTIVE = "active"  # 会话正常进行中
    CLOSED = "closed"  # 会话已关闭
    DELETED = "deleted"  # 会话已删除
    ARCHIVED = "archived"  # 会话已归档

# 创建会话时客户端提交的请求数据结构
class ConversationCreateRequest(BaseModel):
    # 会话标题，... 表示必填，长度限制为 1 到 100 个字符
    title: str = Field(..., min_length=1, max_length=100, description="会话标题")

# 返回单个会话信息的数据结构
class ConversationResponse(BaseModel):
    # 会话唯一 ID，用于查询、更新或删除会话
    conversation_id: str = Field(..., description="会话唯一标识")
    # 会话展示标题
    title: str = Field(..., description="会话标题")
    # 会话当前状态，默认是正常进行中
    status: ConversationStatus = Field(default=ConversationStatus.ACTIVE, description="会话状态")
    # 创建对象时自动记录当前创建时间
    created_at: datetime = Field(default_factory=datetime.now, description="会话创建时间")
    # 最后更新时间，实际项目中新增消息或修改标题后应更新该字段
    updated_at: datetime = Field(default_factory=datetime.now, description="会话最后更新时间")

# 返回某个会话及其全部消息的数据结构
class ConversationMessagesResponse(BaseModel):
    # 所属会话的唯一 ID
    conversation_id: str = Field(..., description="会话唯一标识")
    # 会话消息列表，默认创建新的空列表，避免不同实例共享列表
    messages: list[ChatMessage] = Field(default_factory=list, description="会话消息列表")