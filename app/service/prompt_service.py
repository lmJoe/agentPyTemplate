from app.llm.schemas import LLMMessage
from app.prompts.base import PromptScenario, PromptTemplate
from app.prompts.registry import prompt_registry
from app.prompts.renderer import render_prompt


# PromptService 服务层，负责对外提供 Prompt 的查询、列表获取和渲染功能。它把 prompt_registry（模板管理）与 render_prompt（模板渲染）封装起来，业务代码只需调用这个服务即可

class PromptService:
    """Prompt 模板的查询和渲染服务。"""

    def get_prompt(
        self,
        prompt_id: str,
        version: str = "v1",
    ) -> PromptTemplate:
        """
        根据 Prompt ID 和版本号获取原始 Prompt 模板。

        例如：
            prompt_service.get_prompt("general_chat")
        """
        return prompt_registry.get(
            prompt_id=prompt_id,
            version=version,
        )

    def list_prompts(self) -> list[PromptTemplate]:
        """
        获取当前系统中所有已注册的 Prompt 模板。
        """
        return prompt_registry.list()

    def render_by_prompt_id(
        self,
        prompt_id: str,
        variables: dict,
        version: str = "v1",
    ) -> list[LLMMessage]:
        """
        根据 Prompt ID 获取模板并渲染。

        参数：
            prompt_id: Prompt 的唯一标识，例如 "general_chat"
            variables: 渲染模板使用的变量字典
            version: Prompt 版本，默认 v1

        返回：
            可直接传给大模型接口的 LLMMessage 列表。
        """
        # 先从注册中心获取 Prompt 模板
        prompt = prompt_registry.get(
            prompt_id=prompt_id,
            version=version,
        )

        # 使用传入变量替换模板中的占位符，例如 {user_question}
        return render_prompt(
            prompt=prompt,
            variables=variables,
        )

    def render_by_scenario(
        self,
        scenario: PromptScenario,
        variables: dict,
        version: str = "v1",
    ) -> list[LLMMessage]:
        """
        根据业务场景查找 Prompt 并渲染。

        参数：
            scenario: Prompt 场景，例如 PromptScenario.GENERAL_CHAT
            variables: 渲染模板使用的变量字典
            version: Prompt 版本，默认 v1
        """
        # 按场景从注册中心查找对应 Prompt
        prompt = prompt_registry.find_by_scenario(
            scenario=scenario,
            version=version,
        )

        # 将模板中的变量替换为实际业务数据
        return render_prompt(
            prompt=prompt,
            variables=variables,
        )


# 创建全局 Prompt 服务实例，供其他模块直接导入和使用
prompt_service = PromptService()





# 常见用法：
# 根据 Prompt ID 渲染通用聊天模板
# messages = prompt_service.render_by_prompt_id(
#     prompt_id="general_chat",
#     variables={
#         "user_question": "请介绍一下 Python。",
#     },
# )


# 根据业务场景渲染电商客服模板
# messages = prompt_service.render_by_scenario(
#     scenario=PromptScenario.ECOMMERCE_CUSTOMER_SERVICE,
#     variables={
#         "user_question": "我的订单什么时候发货？",
#         "business_rules": "订单付款后 1～3 个工作日内发货。",
#         "order_info": "订单号：A123，状态：待发货。",
#     },
# )