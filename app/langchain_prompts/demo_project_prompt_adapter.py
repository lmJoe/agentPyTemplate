from langchain_core.messages import BaseMessage

from app.langchain_prompts.service import langchain_prompt_service
from app.prompts.base import PromptScenario
from app.schemas.chat import ChatRequest, MessageRole


# 构建历史消息
def build_history_from_chat_request(
    request: ChatRequest,
) -> list[BaseMessage]:
    """将请求中最后一条消息之前的对话转换为 LangChain 历史消息。"""
    history = []

    for message in request.messages[:-1]:
        if message.role == MessageRole.USER:
            history.append(("human", message.content))

        elif message.role == MessageRole.ASSISTANT:
            history.append(("ai", message.content))

    return history


def build_langchain_messages_from_chat_request(
    request: ChatRequest,
) -> list[BaseMessage]:
    """根据聊天请求组装变量，并渲染对应场景和版本的 Prompt 消息。"""
    latest_user_question = ""

    # 查找最新的用户问题，并从请求中构建历史消息
    for message in reversed(request.messages):
        if message.role == MessageRole.USER:
            latest_user_question = message.content
            break

    # 从请求中获取聊天场景，默认使用通用聊天场景
    scenario = PromptScenario(request.prompt_scenario or PromptScenario.GENERAL_CHAT.value)


    # 组装变量，包括历史消息和用户问题，根据场景添加其他元数据
    variables = {
        "history": build_history_from_chat_request(request),
        "user_question": latest_user_question,
    }

    # 根据场景添加额外的变量
    if scenario == PromptScenario.ECOMMERCE_CUSTOMER_SERVICE:
        variables["business_rules"] = request.metadata.get(
            "business_rules",
            "暂无额外业务规则。",
        )
        variables["order_info"] = request.metadata.get(
            "order_info",
            "用户未提供订单信息。",
        )

    # 检索问答场景额外变量
    if scenario == PromptScenario.RAG_QA:
        variables["retrieved_context"] = request.metadata.get(
            "retrieved_context",
            "暂无检索上下文。",
        )

    # 代理规划场景额外变量
    if scenario == PromptScenario.AGENT_PLANNER:
        variables["user_goal"] = latest_user_question
        variables["available_tools"] = request.metadata.get(
            "available_tools",
            "暂无可用工具。",
        )
        variables["constraints"] = request.metadata.get(
            "constraints",
            "无。",
        )

    # 渲染对应场景和版本的 Prompt 消息列表
    return langchain_prompt_service.render_messages_by_scenario(
        scenario=scenario,
        version=request.prompt_version or "v1",
        variables=variables,
    )
