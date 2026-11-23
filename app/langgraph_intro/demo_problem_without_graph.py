


# 客服处理示例，没有使用 LangGraph。
# 出现的问题
# 逻辑散落
# 状态散落
# 难观察
# 难恢复
# 难中断
# 难复用

def handle_customer_request_without_graph(user_question: str) -> str:
    """
    这是一个没有 LangGraph 的伪代码示例。
    
        问题：
        1. if/else 很快变复杂。
        2. 状态散落在局部变量里。
        3. 中断恢复很难。
        4. 人工确认很难插入。
        5. 每一步的输入输出不好追踪。



    不使用 LangGraph 的客服处理示例。

    这个函数用一连串 if/else 来处理用户问题，展示了这类写法的局限：
    1. 条件分支增加后，流程容易变复杂。
    2. 流程状态保存在多个局部变量中，不便于统一管理。
    3. 程序中断后，很难从上次的状态继续处理。
    4. 不容易在流程中暂停并等待人工确认。
    5. 不会自动记录每一步的输入、输出和执行情况。
    """
    # 初始化流程中会用到的状态变量
    intent = None
    order_id = None
    order_info = None
    policy_answer = None
    need_human_confirm = False

    # 根据关键词粗略判断用户意图
    if "退款" in user_question:
        intent = "refund"
    elif "订单" in user_question or "物流" in user_question:
        intent = "query_order"
    else:
        intent = "general_chat"

    # 普通问题不需要查询订单，直接返回
    if intent == "general_chat":
        return "这是一个普通问题，可以走普通 Chat。"

    # 退款或订单查询需要先从问题中找到订单号
    if intent in ["refund", "query_order"]:
        if "10001" in user_question:
            order_id = "10001"
        elif "10002" in user_question:
            order_id = "10002"
        else:
            # 没有识别到订单号时，请用户补充信息
            return "请您提供订单号，我帮您继续处理。"

    # 模拟查询订单信息：这里只支持两个写死的订单号
    if order_id == "10001":
        order_info = {
            "order_id": "10001",
            "status": "shipped",       # 内部状态值：已发货
            "status_text": "已发货",   # 展示给用户的状态文字
        }
    elif order_id == "10002":
        order_info = {
            "order_id": "10002",
            "status": "paid",               # 内部状态值：已付款，尚未发货
            "status_text": "已付款，待发货",
        }
    else:
        # 订单号格式正确，但没有查到对应订单
        return "没有查询到该订单，请检查订单号是否正确。"

    # 只有退款请求才需要根据订单状态生成退款政策说明
    if intent == "refund":
        if order_info["status"] == "paid":
            policy_answer = "订单未发货时，可以申请取消订单并退款。"
        elif order_info["status"] == "shipped":
            policy_answer = "订单已发货后，需要收到商品后再发起退货退款申请。"
        else:
            # 其他状态下，建议交由人工判断
            policy_answer = "根据当前状态，建议转人工确认。"

    # 人工确认分支：当前示例中 need_human_confirm 始终为 False，
    # 因此这段代码不会执行，除非前面的流程将它设置为 True。
    if need_human_confirm:
        return "该请求需要人工客服确认，我先帮您创建工单。"

    # 退款请求：返回订单状态和对应的退款建议
    if intent == "refund":
        return (
            f"您的订单 {order_info['order_id']} 当前状态是：{order_info['status_text']}。"
            f"{policy_answer}"
        )

    # 普通订单查询：返回订单状态
    return (
        f"您的订单 {order_info['order_id']} 当前状态是：{order_info['status_text']}。"
    )


def main():
    # 准备三个示例问题，分别覆盖退款、订单查询和缺少订单号的情况
    questions = [
        "我的订单 10002 还没发货，这种情况可以退款吗？",
        "帮我查一下订单 10001 到哪了？",
        "我要退款，但是忘记订单号了。",
    ]

    # 逐个处理问题，并打印问题和客服回复
    for question in questions:
        print("question:", question)
        print(handle_customer_request_without_graph(question))
        print("=" * 80)  # 分隔不同示例的输出


# 直接运行这个 Python 文件时，执行 main()；
# 如果这个文件是被其他模块导入，则不自动运行示例。
if __name__ == "__main__":
    main()