from langchain_core.messages import BaseMessage
from langchain_core.prompt_values import ChatPromptValue

from app.langchain_prompts.registry import (
    LangChainPromptDefinition,
    langchain_prompt_registry,
)
from app.prompts.base import PromptScenario


# LangChain Prompt 服务类
class LangChainPromptService:

    # 按 Prompt ID 和版本查找定义，并返回 LangChainPromptDefinition
    def get_by_prompt_id(
        self,
        prompt_id: str,
        version: str = "v1",
    ) -> LangChainPromptDefinition:
        return langchain_prompt_registry.get_by_prompt_id(
            prompt_id=prompt_id,
            version=version,
        )


    # 按场景和版本查找 Prompt 定义，同样由注册表完成查找
    def get_by_scenario(
        self,
        scenario: PromptScenario,
        version: str = "v1",
    ) -> LangChainPromptDefinition:
        return langchain_prompt_registry.get_by_scenario(
            scenario=scenario,
            version=version,
        )

    
    # 调用 render_by_prompt_id 渲染 Prompt，然后返回其中的 messages 列表，类型是 list[BaseMessage]
    def render_by_prompt_id(
        self,
        prompt_id: str,
        variables: dict,
        version: str = "v1",
    ) -> ChatPromptValue:
        definition = self.get_by_prompt_id(
            prompt_id=prompt_id,
            version=version,
        )

        return definition.prompt.invoke(variables)


    # 调用 render_by_prompt_id 渲染 Prompt，然后返回其中的 messages 列表，类型是 list[BaseMessage]
    def render_messages_by_prompt_id(
        self,
        prompt_id: str,
        variables: dict,
        version: str = "v1",
    ) -> list[BaseMessage]:
        prompt_value = self.render_by_prompt_id(
            prompt_id=prompt_id,
            variables=variables,
            version=version,
        )

        return prompt_value.messages

    # 先按场景找到 Prompt，再填入 variables 并渲染，返回 ChatPromptValue
    def render_by_scenario(
        self,
        scenario: PromptScenario,
        variables: dict,
        version: str = "v1",
    ) -> ChatPromptValue:
        definition = self.get_by_scenario(
            scenario=scenario,
            version=version,
        )

        return definition.prompt.invoke(variables)


    # 调用 render_by_scenario，并从渲染结果中提取 messages 列表
    def render_messages_by_scenario(
        self,
        scenario: PromptScenario,
        variables: dict,
        version: str = "v1",
    ) -> list[BaseMessage]:
        prompt_value = self.render_by_scenario(
            scenario=scenario,
            variables=variables,
            version=version,
        )

        return prompt_value.messages

    # 遍历注册表中的 Prompt 定义，把每个定义整理成字典列表，包含 ID、名称、场景、版本、描述、是否启用，以及输入变量、可选变量、元数据和标签等信息。
    def list_prompts(self) -> list[dict]:
        return [
            {
                "prompt_id": definition.prompt_id,
                "name": definition.name,
                "scenario": definition.scenario.value,
                "version": definition.version,
                "description": definition.description,
                "enabled": definition.enabled,
                "input_variables": definition.prompt.input_variables,
                "optional_variables": definition.prompt.optional_variables,
                "metadata": definition.prompt.metadata,
                "tags": definition.prompt.tags,
            }
            for definition in langchain_prompt_registry.list()
        ]

# 创建了一个服务实例，供项目其他代码直接导入和使用。所有方法默认使用版本 "v1"。
langchain_prompt_service = LangChainPromptService()