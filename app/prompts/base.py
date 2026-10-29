from enum import Enum  # 用于定义枚举类型

from pydantic import BaseModel, Field  # Pydantic 数据模型与字段配置


# 消息角色枚举：限定每条消息的发送身份
class PromptRole(str, Enum):
    SYSTEM = "system"        # 系统提示词
    USER = "user"            # 用户消息
    ASSISTANT = "assistant"  # 助手回复


# Prompt 的使用场景枚举
class PromptScenario(str, Enum):
    GENERAL_CHAT = "general_chat"                        # 通用对话
    ECOMMERCE_CUSTOMER_SERVICE = "ecommerce_customer_service"  # 电商客服
    RAG_QA = "rag_qa"                                    # RAG 检索增强问答
    AGENT_PLANNER = "agent_planner"                      # Agent 任务规划


# 单条 Prompt 消息模板
class PromptMessageTemplate(BaseModel):
    # 消息角色，必须是 PromptRole 中定义的值
    role: PromptRole = Field(..., description="消息角色")

    # 消息文本模板；不能为空
    template: str = Field(..., min_length=1, description="消息模板")


# 完整的 Prompt 模板定义
class PromptTemplate(BaseModel):
    # Prompt 的唯一标识，例如：customer_service_v1
    prompt_id: str = Field(..., description="Prompt ID")

    # Prompt 的名称，便于展示和管理
    name: str = Field(..., description="Prompt 名称")

    # 此 Prompt 对应的业务使用场景
    scenario: PromptScenario = Field(..., description="使用场景")

    # 模板版本号；未传入时默认使用 v1
    version: str = Field(default="v1", description="Prompt 版本")

    # 模板说明；未传入时默认为空字符串
    description: str = Field(default="", description="说明")

    # 消息模板列表，至少需要包含一条消息
    messages: list[PromptMessageTemplate] = Field(
        ...,
        min_length=1,
        description="消息模板列表",
    )

    # 渲染模板时必须提供的变量名列表。
    # default_factory=list 避免多个实例共享同一个列表对象。
    required_variables: list[str] = Field(
        default_factory=list,
        description="必填变量",
    )