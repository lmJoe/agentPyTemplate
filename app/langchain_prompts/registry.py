from pydantic import BaseModel, ConfigDict, Field
from langchain_core.prompts import ChatPromptTemplate

# 导入枚举类型和 Prompt 模板定义
from app.prompts.base import PromptScenario

# 导入所有 Prompt 模板定义文件中的 Prompt 模板
from app.langchain_prompts.templates import (
    AGENT_PLANNER_PROMPT,
    ECOMMERCE_CUSTOMER_SERVICE_PROMPT,
    GENERAL_CHAT_PROMPT,
    RAG_QA_PROMPT,
)

# 定义 LangChain Prompt 定义模型
class LangChainPromptDefinition(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True) # 允许任意类型的数据字段

    prompt_id: str = Field(..., description="Prompt ID")
    name: str = Field(..., description="Prompt 名称")
    scenario: PromptScenario = Field(..., description="Prompt 场景") # 枚举类型，限定 Prompt 的使用场景
    version: str = Field(default="v1", description="Prompt 版本")
    description: str = Field(default="", description="Prompt 描述")
    prompt: ChatPromptTemplate = Field(..., description="LangChain ChatPromptTemplate") # LangChain 的 Prompt 模板
    enabled: bool = Field(default=True, description="是否启用") # 是否启用该 Prompt 模板

# 定义 LangChain Prompt 注册表类，用于管理所有注册的 Prompt 模板定义
class LangChainPromptRegistry:
    
    def __init__(self):
        self._prompts: dict[str, LangChainPromptDefinition] = {}

    # 定义了一个 register 方法，用来把一个提示词定义对象存入注册表中。

    def register(self, definition: LangChainPromptDefinition):

        # 从 definition 中读取 prompt_id 和 version，传给 _build_key() 生成唯一键
        key = self._build_key(
            prompt_id=definition.prompt_id,
            version=definition.version,
        )

        # 把 definition 存到 self._prompts 字典中，键就是刚生成的键。
        self._prompts[key] = definition

    
    # 定义了 get_by_scenario 方法，用来按场景和版本查找已启用的 Prompt 定义
    def get_by_scenario(
        self,
        scenario: PromptScenario,
        version: str = "v1",
    ) -> LangChainPromptDefinition:
        for definition in self._prompts.values():
            if definition.scenario == scenario and definition.version == version and definition.enabled:
                return definition

        raise KeyError(f"未找到场景 Prompt：{scenario}@{version}")

    # 定义了 list 方法，用来返回所有已注册的 Prompt 定义
    def list(self) -> list[LangChainPromptDefinition]:
        return list(self._prompts.values())

    # 定义了私有方法 _build_key，用来生成一个由 prompt_id 和 version 组成的唯一键。
    def _build_key(
        self,
        prompt_id: str,
        version: str,
    ) -> str:
        return f"{prompt_id}:{version}"


# 初始化 LangChain Prompt 注册表实例，并添加几个预设的 Prompt 定义对象。
langchain_prompt_registry = LangChainPromptRegistry()


langchain_prompt_registry.register(
    LangChainPromptDefinition(
        prompt_id="general_chat",
        name="通用聊天 Prompt",
        scenario=PromptScenario.GENERAL_CHAT,
        version="v1",
        description="用于普通 AI Chat 问答。",
        prompt=GENERAL_CHAT_PROMPT,
    )
)

langchain_prompt_registry.register(
    LangChainPromptDefinition(
        prompt_id="ecommerce_customer_service",
        name="电商客服 Prompt",
        scenario=PromptScenario.ECOMMERCE_CUSTOMER_SERVICE,
        version="v1",
        description="用于跨境电商客服场景。",
        prompt=ECOMMERCE_CUSTOMER_SERVICE_PROMPT,
    )
)

langchain_prompt_registry.register(
    LangChainPromptDefinition(
        prompt_id="rag_qa",
        name="RAG 问答 Prompt",
        scenario=PromptScenario.RAG_QA,
        version="v1",
        description="用于企业知识库问答。",
        prompt=RAG_QA_PROMPT,
    )
)

langchain_prompt_registry.register(
    LangChainPromptDefinition(
        prompt_id="agent_planner",
        name="Agent 规划 Prompt",
        scenario=PromptScenario.AGENT_PLANNER,
        version="v1",
        description="用于 Agent 任务规划。",
        prompt=AGENT_PLANNER_PROMPT,
    )
)