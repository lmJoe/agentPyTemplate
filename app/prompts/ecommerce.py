from app.prompts.base import (
    PromptMessageTemplate,  # 单条消息模板的数据模型
    PromptRole,             # 消息角色枚举：SYSTEM / USER / ASSISTANT
    PromptScenario,         # Prompt 使用场景枚举
    PromptTemplate,         # 完整 Prompt 模板的数据模型
)
# 加入Few-shot
from app.prompts.examples import ECOMMERCE_FEW_SHOT_EXAMPLES

# 跨境电商客服场景的第 1 版 Prompt 模板
ECOMMERCE_CUSTOMER_SERVICE_PROMPT_V1 = PromptTemplate(
    # Prompt 的唯一标识，用于程序检索和管理
    prompt_id="ecommerce_customer_service",

    # 面向管理后台或开发者展示的名称
    name="跨境电商客服助手",

    # 标记该模板适用的业务场景
    scenario=PromptScenario.ECOMMERCE_CUSTOMER_SERVICE,

    # 模板版本号，后续可新增 v2、v3 等版本
    version="v1",

    # 对模板用途的简要说明
    description="用于跨境电商客服场景，处理订单、物流、售后等问题。",

    # 渲染模板时必须传入的变量。
    # 缺少其中任意变量时，变量校验逻辑会抛出异常。
    required_variables=[
        "user_question",  # 用户提出的客服问题
        "business_rules", # 平台的业务规则，例如退款、物流政策
        "order_info",     # 当前用户订单的相关信息
    ],

    # 定义发送给大模型的消息列表
    messages=[
        # SYSTEM 消息：定义 AI 的身份、职责、边界与回复原则
        PromptMessageTemplate(
            role=PromptRole.SYSTEM,
            template=(
              "你是一个跨境电商平台的专业客服助手。\n"
              "\n"
              "你的职责：\n"
              "1. 帮助用户解答订单、物流、退款、售后相关问题。\n"
              "2. 回答要礼貌、清晰、简洁。\n"
              "3. 如果需要订单号，但用户没有提供，要先引导用户提供订单号。\n"
              "4. 不能编造订单状态、物流单号、退款进度。\n"
              "5. 如果订单信息为空或不足，要明确说明无法确认，并引导用户补充信息。\n"
              "6. 如果问题超出客服范围，要建议用户转人工客服。\n"
              "\n"
              "业务规则：\n"
              "{business_rules}\n"
              "\n"
              "参考示例：\n"
              f"{ECOMMERCE_FEW_SHOT_EXAMPLES}"
          )
        ),

        # USER 消息：注入用户问题与订单信息，并请求模型组织回复
        PromptMessageTemplate(
            role=PromptRole.USER,
            template=(
                # 运行时替换为用户输入的问题
                "用户问题：\n"
                "{user_question}\n"
                "\n"
                # 运行时替换为订单详情；可包括订单号、商品、物流和退款状态等
                "订单信息：\n"
                "{order_info}\n"
                "\n"
                "请根据以上信息回复用户。"
            ),
        ),
    ],
)