from app.prompts.agent import AGENT_PLANNER_PROMPT_V1
from app.prompts.base import PromptScenario, PromptTemplate
from app.prompts.ecommerce import ECOMMERCE_CUSTOMER_SERVICE_PROMPT_V1
from app.prompts.rag import RAG_QA_PROMPT_V1
from app.prompts.templates import GENERAL_CHAT_PROMPT_V1


# Prompt 注册中心（Registry）：统一保存、查询和按业务场景查找不同版本的 Prompt 模板



class PromptRegistry:
    """用于统一注册和管理 Prompt 模板。"""

    def __init__(self):
        # 字典结构：
        # {
        #     "general_chat@v1": PromptTemplate(...),
        #     "rag_qa@v1": PromptTemplate(...),
        # }
        self._prompts: dict[str, PromptTemplate] = {}

    def register(self, prompt: PromptTemplate):
        """注册一个 Prompt 模板。"""
        # 使用「Prompt ID + 版本号」作为唯一键
        key = self._build_key(prompt.prompt_id, prompt.version)

        # 若 key 已存在，会用新的 Prompt 覆盖旧的 Prompt
        self._prompts[key] = prompt

    def get(self, prompt_id: str, version: str = "v1") -> PromptTemplate:
        """根据 Prompt ID 和版本号获取指定模板。"""
        key = self._build_key(prompt_id, version)

        # 未找到对应 Prompt 时抛出异常
        if key not in self._prompts:
            raise KeyError(f"Prompt 不存在：{prompt_id}@{version}")

        return self._prompts[key]

    def list(self) -> list[PromptTemplate]:
        """返回当前已注册的全部 Prompt 模板。"""
        return list(self._prompts.values())

    def find_by_scenario(
        self,
        scenario: PromptScenario,
        version: str = "v1",
    ) -> PromptTemplate:
        """根据业务场景和版本号查找 Prompt 模板。"""
        for prompt in self._prompts.values():
            # 场景和版本均匹配时，返回对应模板
            if prompt.scenario == scenario and prompt.version == version:
                return prompt

        # 没有匹配场景的模板时抛出异常
        raise KeyError(f"场景 Prompt 不存在：{scenario}@{version}")

    @staticmethod
    def _build_key(prompt_id: str, version: str) -> str:
        """生成 Prompt 在注册中心中的唯一键。"""
        return f"{prompt_id}@{version}"


# 创建全局 Prompt 注册中心实例
prompt_registry = PromptRegistry()

# 注册各类业务场景的 v1 Prompt 模板
prompt_registry.register(GENERAL_CHAT_PROMPT_V1)
prompt_registry.register(ECOMMERCE_CUSTOMER_SERVICE_PROMPT_V1)
prompt_registry.register(RAG_QA_PROMPT_V1)
prompt_registry.register(AGENT_PLANNER_PROMPT_V1)



# 使用方法

# 1. prompt_registry.get("general_chat", "v1")

# 2. prompt_registry.find_by_scenario(PromptScenario.RAG_QA)