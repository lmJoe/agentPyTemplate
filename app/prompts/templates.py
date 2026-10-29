from app.prompts.base import (
    PromptMessageTemplate,
    PromptRole,
    PromptScenario,
    PromptTemplate,
)
# 定义了一个可复用的“通用聊天助手”Prompt 模板，名称为 GENERAL_CHAT_PROMPT_V1。
# 它包含两条将发送给大模型的消息：
# 1. SYSTEM 消息：规定 AI 的行为，例如优先使用中文、不编造事实、不确定时说明情况、回答清晰简洁。
# 2. USER 消息：模板为 {user_question}，运行时会被用户实际提问替换。
# 它还声明：
# - prompt_id="general_chat"：该 Prompt 的唯一标识。
# - scenario=GENERAL_CHAT：适用于通用聊天场景。
# - version="v1"：当前模板版本。
# - required_variables=["user_question"]：渲染时必须提供 user_question，否则前面那段校验代码会报错

GENERAL_CHAT_PROMPT_V1 = PromptTemplate(
    prompt_id="general_chat",
    name="通用聊天助手",
    scenario=PromptScenario.GENERAL_CHAT,
    version="v1",
    description="用于普通 AI Chat 的基础 Prompt。",
    required_variables=[
        "user_question",
    ],
    messages=[
        PromptMessageTemplate(
            role=PromptRole.SYSTEM,
            template=(
                "你是一个专业、耐心、表达清晰的 AI 助手。\n"
                "回答要求：\n"
                "1. 优先用中文回答。\n"
                "2. 不要编造事实。\n"
                "3. 如果不确定，请明确说明不确定。\n"
                "4. 回答要结构清晰，不要啰嗦。"
            ),
        ),
        PromptMessageTemplate(
            role=PromptRole.USER,
            template="{user_question}",
        ),
    ],
)