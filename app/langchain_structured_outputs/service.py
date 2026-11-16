from pydantic import BaseModel

from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate

from app.core.exceptions import AppException, ErrorCode
from app.core.logging import get_logger
from app.langchain_models.model_factory import LangChainModelFactory
from app.langchain_structured_outputs.schemas import (
    AgentPlanResult,
    IntentClassificationResult,
    RAGAnswerResult,
)
from app.langchain_structured_outputs.retry import parse_with_repair

# 创建 LangChainStructuredOutputService 类
# 这个类负责调用 LangChain 模型，解析结构化输出。
# 它还负责处理重试和修复。
# 目的在于
# 把结构化输出统一管理起来。
# LangChain 负责底层编排。
# Service 负责业务入口和工程治理。


logger = get_logger(__name__)


class LangChainStructuredOutputService:

    # 实现意图识别结构化输出
    async def classify_intent(
        self,
        user_question: str,
        provider: str = "deepseek",
        model_name: str = "deepseek-chat",
    ) -> IntentClassificationResult:
        return await self._run_pydantic_chain(
            schema=IntentClassificationResult,
            provider=provider,
            model_name=model_name,
            task_name="intent_classification",
            system_prompt=(
                "你是一个电商客服意图识别器。\n"
                "你需要识别用户问题属于哪一类意图。\n"
                "不要输出 Markdown，不要输出解释性文字。"
            ),
            human_template="用户问题：{user_question}",
            variables={
                "user_question": user_question,
            },
        )

    # 实现 Agent Plan 结构化输出
    async def generate_rag_answer(
        self,
        user_question: str,
        retrieved_context: str,
        provider: str = "deepseek",
        model_name: str = "deepseek-chat",
    ) -> RAGAnswerResult:
        return await self._run_pydantic_chain(
            schema=RAGAnswerResult,
            provider=provider,
            model_name=model_name,
            task_name="rag_structured_answer",
            system_prompt=(
                "你是一个企业知识库问答助手。\n"
                "只能基于提供的知识库片段回答。\n"
                "如果知识库没有答案，is_answered 必须为 false。\n"
                "citations 只能包含知识库片段中出现的 document_id。\n"
                "不要编造引用。\n"
                "\n"
                "知识库片段：\n"
                "{retrieved_context}"
            ),
            human_template="用户问题：{user_question}",
            variables={
                "user_question": user_question,
                "retrieved_context": retrieved_context,
            },
        )


    # 实现 Agent Plan 结构化输出
    async def plan_agent_task(
        self,
        user_goal: str,
        available_tools: str,
        constraints: str,
        provider: str = "deepseek",
        model_name: str = "deepseek-chat",
    ) -> AgentPlanResult:
        """根据用户目标生成 AI Agent 的任务执行计划。

        调用大模型并将输出约束为 AgentPlanResult 结构：规划步骤只能使用
        available_tools 中列出的工具，信息不足时须规划询问用户的步骤，
        涉及高风险操作时需标记人工确认。

        Args:
            user_goal: 用户的自然语言目标描述。
            available_tools: 可用工具清单（名称与用途说明），模型只能从中选择。
            constraints: 规划时需要遵守的约束条件。
            provider: 模型提供方，默认为 "deepseek"。
            model_name: 模型名称，默认为 "deepseek-chat"。

        Returns:
            AgentPlanResult: 结构化的任务计划，包含目标、是否需要调用工具、
                是否需要人工确认、执行步骤列表以及最终回复风格。
        """
        return await self._run_pydantic_chain(
            schema=AgentPlanResult,
            provider=provider,
            model_name=model_name,
            task_name="agent_plan",
            system_prompt=(
                "你是一个 AI Agent 任务规划器。\n"
                "只能使用 available_tools 中列出的工具。\n"
                "不要编造不存在的工具。\n"
                "如果信息不足，要规划 ask_user 步骤。\n"
                "如果需要高风险操作，need_human_confirm 必须为 true。\n"
                "\n"
                "可用工具：\n"
                "{available_tools}\n"
                "\n"
                "约束条件：\n"
                "{constraints}"
            ),
            human_template="用户目标：{user_goal}",
            variables={
                "user_goal": user_goal,
                "available_tools": available_tools,
                "constraints": constraints,
            },
        )

    # 实现结构化输出解析链
    async def _run_pydantic_chain(
        self,
        schema: type[BaseModel],
        provider: str,
        model_name: str,
        task_name: str,
        system_prompt: str,
        human_template: str,
        variables: dict,
    ):
        """
        执行基于 Pydantic 解析器的结构化输出链。

        将系统提示词与格式指令组装为提示模板，调用指定模型完成推理，
        并通过 PydanticOutputParser 将模型输出解析为给定 schema 的实例。

        Args:
            schema: 目标输出结构的 Pydantic 模型类。
            provider: 模型提供方名称。
            model_name: 使用的模型名称。
            task_name: 任务名称，用于日志标识与错误信息。
            system_prompt: 系统提示词，用于约束模型行为。
            human_template: 用户消息模板，需与 variables 中的占位符对应。
            variables: 填充提示模板的变量字典。

        Returns:
            BaseModel: 解析后的结构化输出实例。

        Raises:
            AppException: 当模型调用或输出解析失败时抛出，错误码为
                STRUCTURED_OUTPUT_PARSE_FAILED。
        """
        parser = PydanticOutputParser(
            pydantic_object=schema,
        )

        prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                (
                    system_prompt
                    + "\n\n"
                    + "你必须严格按照下面格式输出。\n"
                    + "不要输出 Markdown，不要输出额外解释。\n"
                    + "{format_instructions}"
                ),
            ),
            (
                "human",
                human_template,
            ),
        ]).partial(
            format_instructions=parser.get_format_instructions()
        )

        model = LangChainModelFactory.create(
            provider=provider,
            model=model_name,
            temperature=0,
        )

        chain = prompt | model | parser

        # 执行链，捕获异常并记录日志
        logger.info(
            f"langchain_structured_output_start task={task_name} "
            f"schema={schema.__name__} model={model_name}"
        )

        try:
            result = await chain.ainvoke(variables)

        # 捕获异常并记录日志，抛出异常
        except Exception as exc:

            # 记录解析失败日志
            logger.warning(
                f"langchain_structured_output_parse_failed "
                f"task={task_name} error={repr(exc)}"
            )

            # 抛出异常，包含任务名称、schema 名称及错误信息
            raise AppException(
                message="LangChain 结构化输出解析失败",
                code=ErrorCode.STRUCTURED_OUTPUT_PARSE_FAILED,
                status_code=500,
                data={
                    "task": task_name,
                    "schema": schema.__name__,
                    "error": repr(exc),
                },
            ) from exc
        # 记录解析成功日志，返回结果
        logger.info(
            f"langchain_structured_output_success task={task_name} "
            f"schema={schema.__name__}"
        )

        return result

    # 实现结构化输出修复重试
    async def parse_or_repair(
        self,
        raw_text: str,
        schema: type[BaseModel],
        provider: str = "deepseek",
        model_name: str = "deepseek-chat",
    ):
        return await parse_with_repair(
            raw_text=raw_text,
            schema=schema,
            provider=provider,
            model_name=model_name,
        )


langchain_structured_output_service = LangChainStructuredOutputService()