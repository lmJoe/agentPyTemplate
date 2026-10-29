from app.prompts.base import PromptScenario
from app.service.prompt_service import prompt_service



# 使用“跨境电商客服”Prompt，结合用户问题、业务规则和订单信息，生成给大模型使用的消息列表。

def main():
    """渲染跨境电商客服场景的 Prompt。"""

    # 按业务场景找到“跨境电商客服助手”模板，并填充模板变量
    messages = prompt_service.render_by_scenario(
        # 指定使用电商客服场景的 Prompt
        scenario=PromptScenario.ECOMMERCE_CUSTOMER_SERVICE,

        # 模板渲染所需的实际业务数据
        variables={
            # 用户提出的问题，会填入 {user_question}
            "user_question": "我的订单怎么还没发货？",

            # 平台业务规则，会填入 {business_rules}
            "business_rules": (
                "1. 普通商品付款后 48 小时内发货。\n"
                "2. 定制商品付款后 7 个工作日内发货。\n"
                "3. 没有订单号时，不能查询具体物流。"
            ),

            # 当前可查询到的订单信息，会填入 {order_info}
            "order_info": "用户未提供订单号。",
        },
    )

    # 遍历渲染后的消息列表。
    # messages 通常包含一条 system 消息和一条 user 消息。
    for message in messages:
        # 打印消息角色，例如 system、user
        print("role:", message.role)

        # 打印消息正文
        print(message.content)

        # 输出分隔线，便于在终端查看每条消息
        print("=" * 60)


# 仅在该 Python 文件被直接运行时调用 main()。
# 如果它被其他文件 import，则不会自动执行。
if __name__ == "__main__":
    main()